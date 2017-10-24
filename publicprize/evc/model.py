# -*- coding: utf-8 -*-
""" contest models: Contest, Contestant, Donor, and Founder

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""
import decimal
import flask
import random
import re
import sqlalchemy.orm
import string
import werkzeug.exceptions
from ..debug import pp_t
from .. import biv
from .. import common
from .. import controller as ppc
from ..contest import model as pcm
from ..auth import model as pam
from ..controller import db
from .. import ppdatetime

_SEND_INVITE_MAIL_SUBJECT = '2017 Esprit Venture Challenge Voting Link'

_SEND_INVITE_SMS_BODY = 'Vote at {contest} here: {uri}'

_SEND_INVITE_MAIL_BODY = '''Dear Esprit Entrepreneur Attendee:

Thank you for attending the Boulder Chamber's 33rd annual Esprit Entrepreneur
tonight.  After the competition, please help choose the 2017 Esprit Venture
Challenge winner. Your personal voting link is:

{uri}

This link may only be used one time and will go live at 7:00pm.

Thank you for celebrating entrepreneurship in Boulder and helping select the winner
of the $10,000 prize. Any questions can be directed to Corine Waldau
at corine.waldau@boulderchamber.com.

Cheers,
Boulder Chamber Staff
'''


def is_email(v):
    """Only works for validated emails; Differentiating from phone"""
    return '@' in v


def validate_email_or_phone(value):
    import pyisemail
    v = re.sub(r'\s+', '', value or '')
    if v is None or len(v) == 0:
        return None, 'please enter an email or phone'
    if pyisemail.is_email(v):
        return v.lower(), None
    if is_email(v):
        return None, 'invalid email'
    v = re.sub(r'\D', '', v)
    if len(v) == 10:
        return '({}) {}-{}'.format(v[0:3], v[3:6], v[6:]), None
    return None, 'invalid phone'


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
            'displayName': self.display_name,
            'finalistCount': finalistCount,
            'isEventRegistration': ppdatetime.now_in_range(self.submission_start, self.event_voting_end),
            'isEventVoting': self.is_event_voting(),
            'isExpired': self.is_expired(),
            'isJudging': self.is_judging(),
            'isNominating': self.is_nominating(),
            'isPreNominating': ppdatetime.now_before_start(self.submission_start),
            'isPublicVoting': self.is_public_voting(),
            'semiFinalistCount': semiFinalistCount,
            'showAllContestants': ppdatetime.now_in_range(self.submission_start, self.public_voting_end),
            'showFinalists': ppdatetime.now_in_range(self.judging_end, self.event_voting_end) and finalistCount > 0,
            'showSemiFinalists': ppdatetime.now_in_range(self.public_voting_end, self.judging_end) and semiFinalistCount > 0,
            'showWinner': bool(winner),
            'winner_biv_id': winner,
        }

    def get_finalists(self):
        return E15Nominee.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            E15Nominee.is_finalist == True,
        ).order_by(E15Nominee.display_name).all()

    def is_event_voting(self):
        return ppdatetime.now_in_range(self.event_voting_start, self.event_voting_end)

    def is_expired(self):
        return ppdatetime.now_after_end(self.event_voting_end)

    def is_judge(self):
        if self.is_judging():
            return super(E15Contest, self).is_judge()
        return False

    def is_judging(self):
        return ppdatetime.now_in_range(self.judging_start, self.judging_end)

    def is_nominating(self):
        return ppdatetime.now_in_range(self.submission_start, self.submission_end);

    def is_public_voting(self):
        return ppdatetime.now_in_range(self.public_voting_start, self.public_voting_end)

    def is_semi_finalist_submitter(self):
        return len(E15Contest.semi_finalist_nominees_for_user(self)) > 0

    def nominee_pending_for_user(self):
        access_alias = sqlalchemy.orm.aliased(pam.BivAccess)
        for n in E15Nominee.query.select_from(pam.BivAccess, access_alias).filter(
            pam.BivAccess.source_biv_id == self.biv_id,
            pam.BivAccess.target_biv_id == E15Nominee.biv_id,
            pam.BivAccess.target_biv_id == access_alias.target_biv_id,
            access_alias.source_biv_id == flask.session['user.biv_id'],
        ).all():
            # Only should be one public application at a time
            if not (n.is_valid and n.is_public):
                return n, True
        return E15Nominee(), False

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

    def admin_event_votes(self):
        nominees = {}
        for f in self.get_finalists():
            nominees[f.biv_id] = dict(
                display_name=f.display_name,
                count=0,
            )
        votes = []
        total_votes = 0
        total_votes_used = 0
        for vae in E15VoteAtEvent.query.filter(
             E15VoteAtEvent.contest_biv_id == self.biv_id,
        ).order_by(
            E15VoteAtEvent.invite_email_or_phone,
        ).all():
            v = dict(invite_email_or_phone=vae.invite_email_or_phone, nominee='')
            total_votes += 1
            if vae.nominee_biv_id:
                total_votes_used += 1
                n = nominees[vae.nominee_biv_id]
                n['count'] += 1
                v['nominee'] = n['display_name']
            votes.append(v)
        return dict(
            nominees=sorted(
                nominees.values(),
                key=lambda x: x['count'],
                reverse=True,
            ),
            total_votes=total_votes,
            total_votes_used=total_votes_used,
            votes=votes,
            contest=self.display_name,
        )

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
    is_valid = db.Column(db.Boolean, nullable=False)
    youtube_code = db.Column(db.String(500))
    contact_phone = db.Column(db.String(20))
    contact_address = db.Column(db.String(100))
    nominee_desc = db.Column(db.String)
    is_semi_finalist = db.Column(db.Boolean, nullable=False)
    is_finalist = db.Column(db.Boolean, nullable=False)
    is_winner = db.Column(db.Boolean, nullable=False)

    def assert_is_public_or_404(self):
        if not self.is_public:
            werkzeug.exceptions.abort(404)

    def contest(self):
        return  E15Contest.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == E15Contest.biv_id,
            pam.BivAccess.target_biv_id == self.biv_id,
        ).first_or_404()

    def submitter(self):
        return  pam.User.query.select_from(pam.BivAccess).filter(
            pam.BivAccess.source_biv_id == pam.User.biv_id,
            pam.BivAccess.target_biv_id == self.biv_id,
        ).first_or_404()

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


def _invite_nonce():
    # SystemRandom is cryptographically secure
    return ''.join(
        random.SystemRandom().choice(string.ascii_lowercase) for _ in range(24)
    )


class E15VoteAtEvent(db.Model, common.ModelWithDates):
    """An event vote token
    """
    _NONCE_ATTR = 'vote_at_event.invite_nonce'

    biv_id = db.Column(
        db.Numeric(18),
        db.Sequence('e15_vote_at_event_s', start=1019, increment=1000),
        primary_key=True
    )
    contest_biv_id = db.Column(
        db.Numeric(18), db.ForeignKey('e15_contest.biv_id'), nullable=False)
    contest = db.relationship('E15Contest')
    invite_email_or_phone = db.Column(db.String(100), nullable=False)
    # Bit larger than _invite_nonce()
    invite_nonce = db.Column(db.String(32), unique=True, default=_invite_nonce)
    invites_sent = db.Column(db.Integer, nullable=False, default=0)
    nominee_biv_id = db.Column(db.Numeric(18), nullable=True)
    remote_addr = db.Column(db.String(32), nullable=True)
    user_agent = db.Column(db.String(100), nullable=True)
    # Logged in user at the time of vote, may be meaningless
    user_biv_id = db.Column(db.Numeric(18), nullable=True)

    @classmethod
    def create_unless_exists(cls, contest, invite_email_or_phone):
        query=dict(
            contest_biv_id=contest.biv_id,
            invite_email_or_phone=invite_email_or_phone,
        )
        self = cls.query.filter_by(**query).first()
        if self:
            return self, False
        self = cls(**query)
        ppc.db.session.add(self)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAlias(
                biv_id=self.biv_id,
                alias_name=self.invite_nonce,
            ),
        )
        return self, True

    def save_to_session(self):
        flask.session[self._NONCE_ATTR] = self.invite_nonce

    def send_invite(self, force):
        """Email or SMS voting link"""
        uri = self.format_absolute_uri()
        if (
            self.invites_sent > 0 and not force
            or self.invites_sent >= ppc.app().config['PUBLICPRIZE']['MAX_INVITES_SENT']
        ):
            pp_t('NOT sending to={} uri={}', [self.invite_email_or_phone, uri])
            return None
        pp_cfg = ppc.app().config['PUBLICPRIZE']
        assert pp_cfg['TEST_MODE'] or not re.search('/localhost|/127', uri), \
            'uri={}: uri contains local host'
        pp_t('to={} uri={}', [self.invite_email_or_phone, uri])
        msg_args = dict(
            contest=self.contest.display_name,
            uri=uri,
        )
        if pp_cfg['MAIL_SUPPRESS_SEND']:
            pp_t('MAIL_SUPPRESS_SEND=True')
        if is_email(self.invite_email_or_phone):
            import flask_mail
            msg = flask_mail.Message(
                subject=_SEND_INVITE_MAIL_SUBJECT.format(**msg_args),
                sender=(self.contest.display_name, pp_cfg['SUPPORT_EMAIL']),
                recipients=[self.invite_email_or_phone],
                body=_SEND_INVITE_MAIL_BODY.format(**msg_args),
            )
            ppc.mail().send(msg)
        else:
            import twilio.rest
            cfg = pp_cfg['TWILIO']
            c = twilio.rest.TwilioRestClient(**cfg['auth'])
            sms_args = dict(
                to=self.invite_email_or_phone,
                from_=cfg['from'],
                body=_SEND_INVITE_SMS_BODY.format(**msg_args),
            )
            if not pp_cfg['MAIL_SUPPRESS_SEND']:
                c.sms.messages.create(**sms_args)
        self.invites_sent += 1
        return uri

    @classmethod
    def validate_session(cls, contest):
        i = flask.session.get(cls._NONCE_ATTR)
        if not i:
            pp_t('no invite_nonce')
            return False, None
        self = cls.query.filter_by(invite_nonce=i).first()
        if not self:
            pp_t('invite nonce not found, another db?')
            return False, None
        if self.contest_biv_id != contest.biv_id:
            pp_t(
                'nonce={} expect_contest={} actual_contest={}',
                [i, contest.biv_id, self.contest_biv_id],
            )
            return False, None
        return True, self


E15Contest.BIV_MARKER = biv.register_marker(15, E15Contest)
E15Nominee.BIV_MARKER = biv.register_marker(16, E15Nominee)
E15VoteAtEvent.BIV_MARKER = biv.register_marker(19, E15VoteAtEvent)
