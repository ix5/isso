# -*- encoding: utf-8 -*-

import io
import json
import re
import smtplib
import socket
import time

from _thread import start_new_thread
from email.header import Header
from email.mime.text import MIMEText
from email.utils import formatdate
from urllib.parse import quote

import logging
logger = logging.getLogger("isso")

try:
    import uwsgi
except ImportError:
    uwsgi = None

try:
    import requests
except ImportError:
    requests = None

from isso import local


class SMTPConnection(object):

    def __init__(self, conf):
        self.conf = conf

    def __enter__(self):
        klass = (smtplib.SMTP_SSL if self.conf.get(
            'security') == 'ssl' else smtplib.SMTP)
        self.client = klass(host=self.conf.get('host'),
                            port=self.conf.getint('port'),
                            timeout=self.conf.getint('timeout'))

        if self.conf.get('security') == 'starttls':
            import ssl
            self.client.starttls(context=ssl.create_default_context())

        username = self.conf.get('username')
        password = self.conf.get('password')
        if username and password:
            self.client.login(username, password)

        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.quit()


class SMTP(object):

    def __init__(self, isso):

        self.isso = isso
        self.conf = isso.conf.section("smtp")
        self.public_endpoint = isso.conf.get("server", "public-endpoint") or local("host")
        self.admin_notify = any((n in ("smtp", "SMTP")) for n in isso.conf.getlist("general", "notify"))
        self.reply_notify = isso.conf.getboolean("general", "reply-notifications")

        # test SMTP connectivity
        try:
            with SMTPConnection(self.conf):
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            logger.exception("unable to connect to SMTP server")

        if uwsgi:
            def spooler(args):
                try:
                    self._sendmail(args[b"subject"].decode("utf-8"),
                                   args["body"].decode("utf-8"),
                                   args[b"to"].decode("utf-8"))
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __iter__(self):
        yield "comments.new:after-save", self.notify_new
        yield "comments.activate", self.notify_activated

    def format(self, thread, comment, parent_comment, recipient=None, admin=False):

        rv = io.StringIO()

        author = comment["author"] or "Anonymous"
        if admin and comment["email"]:
            author += " <%s>" % comment["email"]

        rv.write(author + " wrote:\n")
        rv.write("\n")
        rv.write(comment["text"] + "\n")
        rv.write("\n")

        if admin:
            if comment["website"]:
                rv.write("User's URL: %s\n" % comment["website"])

            rv.write("IP address: %s\n" % comment["remote_addr"])

        rv.write("Link to comment: %s\n" %
                 (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
        rv.write("\n")
        rv.write("---\n")

        if admin:
            uri = self.public_endpoint + "/id/%i" % comment["id"]
            key = self.isso.sign(comment["id"])

            rv.write("Delete comment: %s\n" % (uri + "/delete/" + key))

            if comment["mode"] == 2:
                rv.write("Activate comment: %s\n" % (uri + "/activate/" + key))

        else:
            uri = self.public_endpoint + "/id/%i" % parent_comment["id"]
            key = self.isso.sign(('unsubscribe', recipient))

            rv.write("Unsubscribe from this conversation: %s\n" % (uri + "/unsubscribe/" + quote(recipient) + "/" + key))

        rv.seek(0)
        return rv.read()

    def notify_new(self, thread, comment):
        if self.admin_notify:
            body = self.format(thread, comment, None, admin=True)
            subject = "New comment posted"
            if thread['title']:
                subject = "%s on %s" % (subject, thread["title"])
            self.sendmail(subject, body, thread, comment)

        if comment["mode"] == 1:
            self.notify_users(thread, comment)

    def notify_activated(self, thread, comment):
        self.notify_users(thread, comment)

    def notify_users(self, thread, comment):
        if self.reply_notify and "parent" in comment and comment["parent"] is not None:
            # Notify interested authors that a new comment is posted
            notified = []
            parent_comment = self.isso.db.comments.get(comment["parent"])
            comments_to_notify = [parent_comment] if parent_comment is not None else []
            comments_to_notify += self.isso.db.comments.fetch(thread["uri"], mode=1, parent=comment["parent"])
            for comment_to_notify in comments_to_notify:
                email = comment_to_notify["email"]
                if "email" in comment_to_notify and comment_to_notify["notification"] and email not in notified \
                        and comment_to_notify["id"] != comment["id"] and email != comment["email"]:
                    body = self.format(thread, comment, parent_comment, email, admin=False)
                    subject = "Re: New comment posted on %s" % thread["title"]
                    self.sendmail(subject, body, thread, comment, to=email)
                    notified.append(email)

    def sendmail(self, subject, body, thread, comment, to=None):
        to = to or self.conf.get("to")
        if not subject:
            # Fallback, just in case as an empty subject does not work
            subject = 'isso notification'
        if uwsgi:
            uwsgi.spool({b"subject": subject.encode("utf-8"),
                         b"body": body.encode("utf-8"),
                         b"to": to.encode("utf-8")})
        else:
            start_new_thread(self._retry, (subject, body, to))

    def _sendmail(self, subject, body, to_addr):

        from_addr = self.conf.get("from")

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(subject, 'utf-8')

        with SMTPConnection(self.conf) as con:
            con.sendmail(from_addr, to_addr, msg.as_string())

    def _retry(self, subject, body, to):
        for x in range(5):
            try:
                self._sendmail(subject, body, to)
            except smtplib.SMTPConnectError:
                time.sleep(60)
            else:
                break


class Telegram(object):

    def __init__(self, conf):
        self.conf = conf.section("telegram")
        self.chat_id = self.conf.get('chat_id')
        token = self.conf.get('token')
        self.telegram_api = 'https://api.telegram.org/bot{}/sendMessage'.format(token)

    def __iter__(self):

        yield "comments.new:new-thread", self._new_thread
        yield "comments.new:finish", self._new_comment
        yield "comments.edit", self._edit_comment
        yield "comments.delete", self._delete_comment

    def _sanitize(self, message):
        # Need to strip elements Telegram hates
        # See https://core.telegram.org/bots/api#html-style
        allowed = ["b", "i", "u", "s", "a", "code", "pre"]
        sanitized_msg = message
        # Preserve some emphasis that was mis-rendered by misaka
        sanitized_msg = sanitized_msg.replace(
            "<strong>", "<b>").replace("</strong>", "</b>")
        for m in re.findall(r"(</?\w+>)", message):
            # Only tag content:
            stripped = m.lstrip("<").rstrip(">").lstrip("/")
            # Links should be ok, however attrs may appear in any order
            if any((stripped.startswith('a href'),
                    stripped.startswith('a rel="noopener"'),
                    stripped.startswith('a rel="nofollow"'))):
                continue
            if stripped not in allowed:
                sanitized_msg = sanitized_msg.replace(m, "")
        return sanitized_msg

    def _post_tg(self, message):
        if not requests:
            logger.warn("Need requests package for posting to Telegram API!")
            return
        r = requests.post(self.telegram_api,
                          data={
                              'chat_id': self.chat_id,
                              'text': message,
                              'parse_mode': 'HTML'
                          })
        # Response should look like:
        # b'{"ok":true,"result":...}
        logger.info("Got response from TG API: {}".format(r.content))
        r_dict = json.loads(r.content)
        if r_dict.get("ok") is True:
            logger.info("Posting to Telegram successful")
        else:
            logger.warn("Posting to Telegram failed! {}".format(r_dict))

    def _new_thread(self, thread):
        pass
        # Don't hook this up for now, do I really want to be spammed by meaningless ids?
        # Also, isso fails to fetch the thread title anyway
        #self._post_tg("New thread! {id}: {title}".format(**thread))

    def _new_comment(self, thread, comment):
        # Make sure that db.comments object is not inadvertently
        # modified for acutal API functions
        comment["sanitized_text"] = self._sanitize(comment["text"])
        msg = "New comment!\n\n"
        msg += "<b>Author</b>: {}\n".format(comment.get("author"))
        if comment.get("website"):
            msg += "<b>Website:</b> {}\n".format(comment["website"])
        if comment.get("email"):
            msg += "<b>Email:</b> {}\n".format(comment["email"])
        msg += "<b>Thread:</b> https://{}\n".format(thread.get("uri"))
        msg += "<b>Content</b>:\n{}".format(comment["sanitized_text"])
        self._post_tg(msg)

    def _edit_comment(self, comment):
        # Make sure that db.comments object is not inadvertently
        # modified for acutal API functions
        comment["sanitized_text"] = self._sanitize(comment["text"])
        msg = "Comment edited:\n\n"
        msg += "<b>Author</b>: {}\n".format(comment.get("author"))
        if comment.get("website"):
            msg += "<b>Website:</b> {}\n".format(comment["website"])
        if comment.get("email"):
            msg += "<b>Email:</b> {}\n".format(comment["email"])
        msg += "<b>Content</b>:\n{}".format(comment["sanitized_text"])
        self._post_tg(msg)

    def _delete_comment(self, id):
        pass
        # Don't hook this up for now
        #self._post_tg("Comment deleted: {}".format(id))


class Stdout(object):

    def __init__(self, conf):
        pass

    def __iter__(self):

        yield "comments.new:new-thread", self._new_thread
        yield "comments.new:finish", self._new_comment
        yield "comments.edit", self._edit_comment
        yield "comments.delete", self._delete_comment
        yield "comments.activate", self._activate_comment

        yield "reactions.new:new-thread", self._new_thread
        yield "reactions.new:finish", self._new_reaction

    def _new_thread(self, thread):
        logger.info("new thread %(id)s: %(title)s" % thread)

    def _new_comment(self, thread, comment):
        logger.info("comment created: %s", json.dumps(comment))

    def _edit_comment(self, comment):
        logger.info('comment %i edited: %s',
                    comment["id"], json.dumps(comment))

    def _delete_comment(self, id):
        logger.info('comment %i deleted', id)

    def _activate_comment(self, thread, comment):
        logger.info("comment %(id)s activated" % thread)

    def _new_reaction(self, thread, rv):
        logger.info("new reaction id: %d (%d times) for thread: %s" % (
            rv['id'], rv['count'], thread['uri']))
