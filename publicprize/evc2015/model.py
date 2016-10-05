# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import decimal
import random
import re

import flask
import sqlalchemy.orm

from .. import biv
from .. import common
from .. import controller
from ..contest import model as pcm
from ..auth import model as pam
from ..controller import db
from .. import ppdatetime

def _datetime_column():
    return db.Column(db.DateTime(timezone=False), nullable=False)


class E15Contest(db.Model, pcm.ContestBase):
    """contest database model.
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('e15contest_s', start=1015, increment=1000),
        primary_key=True
    )
    time_zone = db.Column(db.String, nullable=False)
    event_voting_end = _datetime_column()
    event_voting_start = _datetime_column()
    judging_end = _datetime_column()
    judging_start = _datetime_column()
    public_voting_end = _datetime_column()
    public_voting_start = _datetime_column()
    submission_end = _datetime_column()
    submission_start = _datetime_column()

    def contest_info(self):
        winner = self._winner_biv_id()
        # TODO: check to make sure show*/is* aren't conflicting (one second overlap)
        #    need to detect transtions. If there are no finalists, but showFinalists, then
        #    compute finalists. Probably just want this on any contest page.
        semiFinalistCount = self._count(E15Nominee.is_semi_finalist)
        finalistCount = self._count(E15Nominee.is_finalist)
        return {
            'contestantCount': len(self.public_nominees()),
            'finalistCount': finalistCount,
            'isEventVoting': ppdatetime.now_in_range(self.event_voting_start, self.event_voting_end),
            'isJudging': self.is_judging(),
            'isNominating': ppdatetime.now_in_range(self.submission_start, self.submission_end),
            'isPreNominating': ppdatetime.now_before_start(self.submission_start),
            'isPublicVoting': self.is_public_voting(),
            'semiFinalistCount': semiFinalistCount,
            'showAllContestants': ppdatetime.now_in_range(self.submission_start, self.public_voting_end),
            'showFinalists': ppdatetime.now_in_range(self.judging_end, self.event_voting_end) and finalistCount > 0,
            'showSemiFinalists': ppdatetime.now_in_range(self.public_voting_end, self.judging_end) and semiFinalistCount > 0,
            'showWinner': bool(winner),
            'winner_biv_id': winner,
        }

    def is_expired(self):
        return ppdatetime.now_after_end(self.event_voting_end)

    def is_judge(self):
        if self.is_judging():
            return super(E15Contest, self).is_judge()
        return False

    def is_judging(self):
        return ppdatetime.now_in_range(self.judging_start, self.judging_end)

    def is_public_voting(self):
        return ppdatetime.now_in_range(self.public_voting_start, self.public_voting_end)

    def is_semi_finalist_submitter(self):
        return len(E15Contest.semi_finalist_nominees_for_user(self)) > 0

    def public_nominees(self):
        return E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            E15Nominee.is_public == True,
        ).all()

    def semi_finalist_nominees_for_user(self):
        if not flask.session.get('user.is_logged_in'):
            return []
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        return E15Nominee.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            pam.BivAccess.target_biv_id == access_alias.target_biv_id,
            access_alias.source_biv_id == flask.session['user.biv_id'],
            E15Nominee.is_semi_finalist == True,
        ).all()

    def tally_all_scores(self):
        res = []
        total_votes = 0
        total_rank_scores = 0
        for nominee in self.public_nominees():
            ranks = nominee.get_judge_ranks()
            vote_score = nominee.tally_votes()
            total_votes += vote_score
            rank_score = nominee.tally_judge_ranks()
            total_rank_scores += rank_score
            res.append({
                'biv_id': nominee.biv_id,
                'display_name': nominee.display_name,
                'judge_ranks': '( {} )'.format(', '.join(map(str, ranks))),
                'votes': vote_score,
                'judge_score': rank_score,
            })
        return res

    def _count(self, field):
        return E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            field == True,
        ).count()

    def _winner_biv_id(self):
        res = E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            E15Nominee.is_winner == True,
        ).first()
        return res.biv_id if res else None


class E15EventVoter(db.Model, common.ModelWithDates):
    """event voter database mode.
    """
    __tablename__ = 'e15_event_voter'
    contest_biv_id = db.Column(db.Numeric(18), primary_key=True)
    user_email = db.Column(db.String(100), nullable=False, primary_key=True)
    nominee_biv_id = db.Column(db.Numeric(18))


class E15Nominee(db.Model, pcm.NomineeBase):
    """nominatee database model.
    """
    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('e15nominee_s', start=1016, increment=1000),
        primary_key=True
    )
    youtube_code = db.Column(db.String(500))
    nominee_desc = db.Column(db.String)
    is_semi_finalist = db.Column(db.Boolean, nullable=False)
    is_finalist = db.Column(db.Boolean, nullable=False)
    is_winner = db.Column(db.Boolean, nullable=False)

    def tally_judge_ranks(self):
        score = 0
        for rank in self.get_judge_ranks():
            score += (pcm.JudgeRank.MAX_RANKS + 1) - rank
        return score

    def tally_votes(self):
        count = 0
        for vote in self.get_votes():
            if vote.vote_status == '1x':
                count += 1
            elif vote.vote_status == '2x':
                count += 2
        return count


E15Contest.BIV_MARKER = biv.register_marker(15, E15Contest)
E15Nominee.BIV_MARKER = biv.register_marker(16, E15Nominee)
