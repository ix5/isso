# -*- encoding: utf-8 -*-

import logging
import time

from isso.utils import Bloomfilter


logger = logging.getLogger("isso")


# Separate reaction table is used because voters field in comments table is
# per-comment, also people should be able to upvote comments and also react to
# posts independently
#
# I _think_ this functionality could also live inside the threads table...
#
# Why not one voters blob for all reactions? Such as:
# | tid | likes | dislikes | thanks | [...] | voters |
# Because then we would deprive users of the possibility of giving more than
# one reaction (thanks _and_ kudos) per thread


class Reactions:
    """Scheme overview:

        | tid (thread id) | id (reaction id) | reactiontype | votes | voters |
        +-----------------+---------------------------------|-------+--------+
        | 1               | 1                | 1            | 2     | BLOB   |
        | 8               | 2                | 1            | 7     | BLOB   |
        +-----------------+---------------------------------|-------+--------+

    The tuple (tid, reactiontype) is unique and thus primary key.
    """

    fields = ['tid', 'id',
              'reactiontype',  # type of reaction: currently 1 = thanks
              'created', 'modified', 'votes', 'voters']

    def __init__(self, db):

        self.db = db
        self.db.execute([
            'CREATE TABLE IF NOT EXISTS reactions (',
            '    tid REFERENCES threads(id), id INTEGER PRIMARY KEY,',
            '    reactiontype INTEGER, created FLOAT NOT NULL, modified FLOAT,',
            '    votes INTEGER, voters BLOB NOT NULL);'])

    def _increase(self, uri, reactiontype, remote_addr):
        rv = self.db.execute([
            'SELECT reactions.id, reactions.votes, reactions.voters',
            '    FROM reactions',
            '    INNER JOIN threads ON threads.uri=?',
            '    AND reactions.tid=threads.id;'],
            (uri,)).fetchone()

        # FIXME: Be overly cautious until this is properly tested
        if rv is None:
            return None

        id, votes, voters = rv

        if id is None:
            return None

        bf = Bloomfilter(bytearray(voters), votes)
        if remote_addr in bf:
            message = '{} denied, remote address: {}'.format("'Thanks'", remote_addr)
            logger.warn('Reactions.thanks(reactiontype=%d): %s', reactiontype, message)
            return {'id': id, 'count': votes, 'increased': False}

        bf.add(remote_addr)
        self.db.execute([
            'UPDATE reactions SET',
            '    votes = votes + 1,',
            '    voters = ?'
            'WHERE id=?;'], (memoryview(bf.array), id))

        # FIXME: double-check shouldn't be necessary, just emit count+1 without
        # triggering another sql query
        cnt = self.db.execute([
            'SELECT votes FROM reactions',
            '    WHERE id=?;'],
            (id,)).fetchone()[0]

        return {'id': id, 'count': cnt, 'increased': False}


    def add(self, uri, r):
        """
        Add new reaction to DB and return a mapping of :attribute:`fields` and
        database values.
        """

        rv = self._increase(uri, r.get('reaction'), r.get('remote_addr'))
        if rv:
            #rv.pop('id')  # TODO: Only return API fields
            return rv

        self.db.execute([
            'INSERT INTO reactions (',
            '    tid, reactiontype, created, modified, votes, voters)',
            'SELECT',
            '    threads.id, ?, ?, ?, ?, ?',
            'FROM threads WHERE threads.uri = ?;'], (
            r.get('reaction'),
            r.get('created') or time.time(), None,
            1,  # votes start at 1
            memoryview(
                Bloomfilter(iterable=[r['remote_addr']]).array),
            uri)
        )

        rv = self.db.execute([
            'SELECT reactions.* FROM reactions',
            '    INNER JOIN threads ON threads.uri=?',
            '    AND reactions.tid=threads.id;'],
            (uri,)).fetchone()

        rv = dict(zip(Reactions.fields, rv))

        return {"id": rv.get("id"), "count": rv.get("votes"), 'increased': True}


    def count(self, uri):
        """
        Return comment count for one ore more urls..
        """

        rv = self.db.execute([
            'SELECT reactions.votes FROM reactions',
            '    INNER JOIN threads ON threads.uri=?',
            '    AND reactions.tid=threads.id;'],
            (uri,)).fetchone()

        try:
            return {"count": rv[0]}
        except (IndexError, TypeError):
            return {"count": 0}
