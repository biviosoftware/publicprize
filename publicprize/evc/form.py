# -*- coding: utf-8 -*-
""" contest forms: HTTP form processing for contest pages

    :copyright: Copyright (c) 2014 Bivio Software, Inc.  All Rights Reserved.
    :license: Apache, see LICENSE for more details.
"""

import datetime
import decimal
import locale
import pytz
import re
import socket
import sys
import urllib.request

import flask
import flask_mail
import flask_wtf
import paypalrestsdk
import paypalrestsdk.exceptions
import wtforms
import wtforms.validators as wtfv

from . import model as pcm
from .. import controller as ppc
from ..auth import model as pam

class Contestant(flask_wtf.Form):
    """Project submission form.

    Fields:
        display_name: project name
        contestant_desc: project summary
        youtube_url: full YouTube video url
        slideshow_url: full SlideShare url
        founder_desc: current user's founder info for this project
        website: project website (optional)
    """
    display_name = wtforms.StringField(
        'Legal Name of Business', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    contestant_desc = wtforms.TextAreaField(
        'Summary of Business, Product and/or Service',
        validators=[wtfv.DataRequired(), wtfv.Length(max=10000)])
    youtube_url = wtforms.StringField(
        'YouTube Video URL', validators=[
            wtfv.DataRequired(), wtfv.Length(max=500)])
    slideshow_url = wtforms.StringField(
        'SlideShare Pitch Deck URL', validators=[
            wtfv.DataRequired(), wtfv.Length(max=500)])
    founder_desc = wtforms.TextAreaField(
        'Your Bio', validators=[wtfv.DataRequired(), wtfv.Length(max=10000)])
    website = wtforms.StringField(
        'Business Website', validators=[wtfv.Length(max=100)])
    tax_id = wtforms.StringField(
        'Business US Tax Id', validators=[
            wtfv.DataRequired(), wtfv.Length(max=30)])
    business_phone = wtforms.StringField(
        'Business Phone', validators=[
            wtfv.DataRequired(), wtfv.Length(max=100)])
    business_address = wtforms.TextAreaField(
        'Business Mailing Address', validators=[
            wtfv.DataRequired(), wtfv.Length(max=500)])
    agree_to_terms = wtforms.BooleanField(
        'Agree to Terms of Service', validators=[wtfv.DataRequired()])
    founder2_name = wtforms.StringField(
        'Other Founder Name', validators=[wtfv.Length(max=100)])
    founder2_desc = wtforms.TextAreaField(
        'Other Founder Bio', validators=[wtfv.Length(max=10000)])
    founder3_name = wtforms.StringField(
        'Other Founder Name', validators=[wtfv.Length(max=100)])
    founder3_desc = wtforms.TextAreaField(
        'Other Founder Bio', validators=[wtfv.Length(max=10000)])

    def execute(self, contest):
        """Validates and creates the contestant model"""
        if self.is_submitted() and self.validate():
            contestant = self._update_models(contest)
            if contestant:
                self._send_mail_to_support(contestant)
                flask.flash(
                    'Thank you for submitting your entry. You will be '
                    'contacted by email when your entry has been reviewed.')
                return flask.redirect(contest.format_uri('contestants'))
        return contest.task_class.render_template(
            contest,
            'submit',
            form=self,
            selected='submit-contestant'
        )

    def validate(self):
        """Performs superclass wtforms validation followed by url
        field validation"""
        super(Contestant, self).validate()
        self._validate_youtube()
        self._validate_slideshare()
        self._validate_website()
        _log_errors(self)
        return not self.errors

    def _add_founder(self, contestant, founder):
        """Creates the founder and links it to the contestant."""
        ppc.db.session.add(founder)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contestant.biv_id,
                target_biv_id=founder.biv_id
            )
        )

    def _add_founders(self, contestant):
        """Add the current user as a founder and any optional founders."""
        founder = pcm.Founder()
        self.populate_obj(founder)
        founder.display_name = flask.session['user.display_name']
        self._add_founder(contestant, founder)
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=flask.session['user.biv_id'],
                target_biv_id=founder.biv_id
            )
        )
        if self.founder2_name.data:
            self._add_founder(contestant, pcm.Founder(
                display_name=str(self.founder2_name.data),
                founder_desc=str(self.founder2_desc.data),
            ))
        if self.founder3_name.data:
            self._add_founder(contestant, pcm.Founder(
                display_name=str(self.founder3_name.data),
                founder_desc=str(self.founder3_desc.data),
            ))

    def _get_url_content(self, url):
        """Performs a HTTP GET on the url.

        Returns False if the url is invalid or not-found"""
        res = None
        if not re.search(r'^http', url):
            url = 'http://' + url
        try:
            req = urllib.request.urlopen(url, None, 30)
            res = req.read().decode(locale.getlocale()[1])
            req.close()
        except urllib.request.URLError:
            return None
        except ValueError:
            return None
        except socket.timeout:
            return None
        return res

    def _send_mail_to_support(self, contestant):
        """Send a notification to support for a new entry"""
        ppc.mail().send(flask_mail.Message(
            'New Entry Submitted: {}'.format(contestant.biv_id),
            recipients=[ppc.app().config['PUBLICPRIZE']['SUPPORT_EMAIL']],
            # TODO(pjm): requires new Flask-Mail for unicode on python 3
            # body='Submitted by: {} {}\nTitle: {}\nReview URL: {}'.format(
            #     flask.session['user.display_name'],
            #     pam.User.query.filter_by(
            #         biv_id=flask.session['user.biv_id']
            #     ).one().user_email,
            #     contestant.display_name,
            #     contestant.format_absolute_uri()
            # )
            body='Submitted by: {}\nReview URL: {}'.format(
                pam.User.query.filter_by(
                    biv_id=flask.session['user.biv_id']
                ).one().user_email,
                contestant.format_absolute_uri()
            )
        ))

    def _slideshare_code(self):
        """Download slideshare url and extract embed code.
        The original url may not have the code.
        ex. www.slideshare.net/Micahseff/game-xplain-pitch-deck-81610
        Adds field errors if the code can not be determined.
        """
        html = self._get_url_content(self.slideshow_url.data)
        if not html:
            self.slideshow_url.errors = [
                'SlideShare URL invalid or unavailable.']
            return None
        match = re.search(r'slideshow/embed_code/(\d+)', html)
        if match:
            return match.group(1)
        self.slideshow_url.errors = [
            'Embed code not found on SlideShare page.']
        return None

    def _update_models(self, contest):
        """Creates the Contestant and Founder models
        and adds BivAccess models to join the contest and Founder models"""
        contestant = pcm.Contestant()
        self.populate_obj(contestant)
        contestant.youtube_code = self._youtube_code()
        contestant.slideshow_code = self._slideshare_code()
        contestant.is_public = \
            ppc.app().config['PUBLICPRIZE']['ALL_PUBLIC_CONTESTANTS']
        contestant.is_under_review = False
        ppc.db.session.add(contestant)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=contestant.biv_id
            )
        )
        self._add_founders(contestant)
        return contestant

    def _youtube_code(self):
        """Ensure the youtube url contains a VIDEO_ID"""
        value = self.youtube_url.data
        # http://youtu.be/a1Y73sPHKxw
        # or https://www.youtube.com/watch?v=a1Y73sPHKxw
        if re.search(r'\?', value) and re.search(r'v\=', value):
            match = re.search(r'(?:\?|\&)v\=(.*?)(&|$)', value)
            if match:
                return match.group(1)
        else:
            match = re.search(r'\/([^\&\?\/]+)$', value)
            if match:
                return match.group(1)
        return None

    def _validate_slideshare(self):
        """Ensures the SlideShare slide deck exists"""
        if self.slideshow_url.errors:
            return
        code = self._slideshare_code()
        if code:
            if not self._get_url_content(
                    'http://www.slideshare.net/slideshow/embed_code/' + code):
                self.slideshow_url.errors = [
                    'Unknown SlideShare ID: ' + code + '.']

    def _validate_website(self):
        """Ensures the website exists"""
        if self.website.errors:
            return
        if self.website.data:
            if not self._get_url_content(self.website.data):
                self.website.errors = ['Website invalid or unavailable.']

    def _validate_youtube(self):
        """Ensures the YouTube video exists"""
        if self.youtube_url.errors:
            return
        code = self._youtube_code()
        if code:
            html = self._get_url_content('http://youtu.be/' + code)
            # TODO(pjm): need better detection for not-found page
            if not html or re.search(r'<title>YouTube</title>', html):
                self.youtube_url.errors = [
                    'Unknown YouTube VIDEO_ID: ' + code + '.']
        else:
            self.youtube_url.errors = ['Invalid YouTube URL.']


class Donate(flask_wtf.Form):
    """Donation form.

    Fields:
        amount: donation amount
    """
    # TODO(pjm): DecimalField doesn't accept '' value...
    amount = wtforms.StringField('Contribution Amount')
    donate5 = wtforms.SubmitField('$5')
    donate25 = wtforms.SubmitField('$25')
    donate100 = wtforms.SubmitField('$100')
    other_amount = wtforms.SubmitField('Other Amount')

    def execute(self, contestant):
        """Validates and redirects to PayPal
        For test credit card payments, use card number: 4736656842918643
        """
        if self.is_submitted() and self.validate():
            url = self._paypal_payment(contestant)
            if url:
                return flask.redirect(url)
        contest = contestant.get_contest()
        return contest.task_class.render_template(
            contest,
            'detail',
            contestant=contestant,
            contestant_url=contestant.format_absolute_uri(),
            contestant_tweet="Help us win! " + contestant.display_name,
            form=self,
        )

    def execute_payment(self, contestant):
        """Handles return task from paypal. Calls paypal with payment and
        payer IDs to complete the transaction."""
        donor = pcm.Donor.unsafe_load_from_session()
        if not donor:
            ppc.app().logger.warn('missing session donor')
            flask.flash('The referenced contribution was already processed.')
            return flask.redirect(contestant.format_uri())
        self._save_payment_info_to_donor(donor)
        payment = paypalrestsdk.Payment({
            'id': donor.paypal_payment_id
        })
        donor.remove_from_session()
        try:
            if payment.execute({'payer_id': donor.paypal_payer_id}):
                donor.donor_state = 'executed'
                ppc.db.session.add(donor)
                return flask.redirect(contestant.format_uri('thank-you'))
            else:
                ppc.app().logger.warn('payment execute failed')
        except paypalrestsdk.exceptions.ClientError as err:
            ppc.app().logger.warn(err)
        except:
            ppc.app().logger.warn(sys.exc_info()[0])
        return flask.redirect(contestant.format_uri())

    def validate(self):
        """Ensure the amount is present and at least $10"""
        super(Donate, self).validate()
        amount = None

        if self.donate5.data:
            amount = 5
        elif self.donate25.data:
            amount = 25
        elif self.donate100.data:
            amount = 100
        elif self.amount.data:
            try:
                if float(self.amount.data) < 10:
                    self.amount.errors = ['Amount must be at least $10.']
                elif float(self.amount.data) > 1000000:
                    self.amount.errors = ['Amount too large.']
            except ValueError:
                self.amount.errors = ['Please enter an amount.']
        else:
            self.amount.errors = ['Please enter an amount.']
            self.amount.raw_data = None
        if amount:
            self.amount.data = decimal.Decimal(amount)
        _log_errors(self)
        return not self.errors

    def _create_donor(self, contestant):
        """Create a new donor model and link to the parent contestant."""
        donor = pcm.Donor()
        self.populate_obj(donor)
        donor.donor_state = 'submitted'
        ppc.db.session.add(donor)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contestant.biv_id,
                target_biv_id=donor.biv_id
            )
        )
        return donor

    def _link_donor_to_user(self, donor):
        """Link the donor model to a user model. Match the donor email with
        the user. If no match, use the current user, if present."""
        if pam.BivAccess.query.select_from(pam.User).filter(
                pam.BivAccess.source_biv_id == pam.User.biv_id,
                pam.BivAccess.target_biv_id == donor.biv_id
        ).count() > 0:
            return
        user = pam.User.query.filter_by(user_email=donor.donor_email).first()
        if not user and flask.session.get('user.is_logged_in'):
            user = pam.User.query.filter_by(
                biv_id=flask.session['user.biv_id']
            ).one()
        if not user:
            return
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=user.biv_id,
                target_biv_id=donor.biv_id
            )
        )

    def _paypal_payment(self, contestant):
        """Call paypal server to create payment record.
        Returns a redirect link to paypal site or None on error."""
        donor = self._create_donor(contestant)
        amount = '%.2f' % float(self.amount.data)
        payment = paypalrestsdk.Payment({
            'intent': 'sale',
            'payer': {
                'payment_method': 'paypal'
            },
            'redirect_urls': {
                'return_url': contestant.format_absolute_uri('donate-done'),
                'cancel_url': contestant.format_absolute_uri('donate-cancel'),
            },
            'transactions': [
                {
                    'amount': {
                        'total': amount,
                        'currency': 'USD',
                    },
                    'item_list': {
                        'items': [
                            {
                                'quantity': 1,
                                'price': amount,
                                'currency': 'USD',
                                'name': '{} contribution, {}'.format(
                                    contestant.display_name,
                                    contestant.get_contest().display_name),
                                'tax': 0
                            }
                        ]
                    }
                }
            ]
        })

        try:
            if payment.create():
                ppc.app().logger.info(payment)
                donor.paypal_payment_id = str(payment.id)
                donor.add_to_session()

                for link in payment.links:
                    if link.method == 'REDIRECT':
                        return str(link.href)
            else:
                ppc.app().logger.warn(payment.error)
        except paypalrestsdk.exceptions.ClientError as err:
            ppc.app().logger.warn(err)
        except:
            ppc.app().logger.warn(sys.exc_info()[0])
        self.amount.errors = [
            'There was an error processing your contribution.']
        return None

    def _save_payment_info_to_donor(self, donor):
        """Get payer info from paypal server, save info to Donor model."""
        try:
            payment = paypalrestsdk.Payment.find(donor.paypal_payment_id)
            info = payment.payer.payer_info
            donor.donor_email = info.email
            donor.display_name = info.first_name + ' ' + info.last_name
        except paypalrestsdk.exceptions.ConnectionError as err:
            ppc.app().logger.warn(err)
        donor.paypal_payer_id = flask.request.args['PayerID']
        donor.donor_state = 'pending_confirmation'
        ppc.db.session.add(donor)
        self._link_donor_to_user(donor)


class Judgement(flask_wtf.Form):
    """Judgement form.

    Fields:
        question(1 .. 6): question score
        question(1 ..6)_comment: comments for survey question
        general_comment: End of survey comments
    """
    def _comment_field(label='Comments'):
        return wtforms.TextAreaField(
            label, validators=[wtfv.Length(max=10000)])

    def _question_field(number):
        return wtforms.RadioField(
            'Question {}'.format(number),
            choices=[
                ('1', 'Unsatisfactory'),
                ('2', 'Improvement Needed'),
                ('3', 'Meets Expectations'),
                ('4', 'Exceeds Expectations')
            ]
        )

    question1 = _question_field('1')
    question1_comment = _comment_field()
    question2 = _question_field('2')
    question2_comment = _comment_field()
    question3 = _question_field('3')
    question3_comment = _comment_field()
    question4 = _question_field('4')
    question4_comment = _comment_field()
    question5 = _question_field('5')
    question5_comment = _comment_field()
    question6 = _question_field('6')
    question6_comment = _comment_field()
    general_comment = _comment_field('General Comments')

    def execute(self, contestant):
        """Saves scores for questions."""
        contest = contestant.get_contest()
        if self.is_submitted():
            if self.validate():
                self._save_scores(contestant)
                flask.flash('Thank you for scoring contestant {}.'.format(
                    contestant.display_name))
                return flask.redirect(
                    contest.format_uri('judging'))
        else:
            self._load_scores(contestant)
        return contest.task_class.render_template(
            contest,
            'judge-contestant',
            sub_base_template=contest.task_class.base_template('detail'),
            contestant=contestant,
            form=self
        )

    @classmethod
    def get_points_for_question(cls, number):
        return pcm.JudgeScore.get_points_for_question(number)

    @classmethod
    def get_text_for_question(cls, number):
        return pcm.JudgeScore.get_text_for_question(number)

    def validate(self):
        """Clear any errors for unselected radio choices."""
        super(Judgement, self).validate()
        for num in range(1, 7):
            self['question{}'.format(num)].errors = None
        _log_errors(self)
        return not self.errors

    def _load_scores(self, contestant):
        """Load scores from database."""
        for num in range(1, 7):
            score = self._unsafe_get_score(contestant, num)
            if not score:
                continue
            self['question{}'.format(num)].data = str(score.judge_score)
            self['question{}_comment'.format(num)].data = score.judge_comment
        question0 = self._unsafe_get_score(contestant, 0)
        if score:
            self.general_comment.data = question0.judge_comment

    def _save_score(self, contestant, num, val, comment):
        """Save a question score to database."""
        score = self._unsafe_get_score(contestant, num)
        if not score:
            score = pcm.JudgeScore()
            score.judge_biv_id = flask.session['user.biv_id']
            score.contestant_biv_id = contestant.biv_id
            score.question_number = int(num)
        score.judge_score = int(val)
        score.judge_comment = comment
        ppc.db.session.add(score)

    def _save_scores(self, contestant):
        """Saves scores to database."""
        for num in range(1, 7):
            val = self['question{}'.format(num)].data
            # TODO(pjm): hack - val may have been coerced to string "None"
            if val is None or val == 'None':
                val = 0
            self._save_score(contestant, num, val,
                             str(self['question{}_comment'.format(num)].data))
        self._save_score(contestant, 0, 0, str(self.general_comment.data))

    def _unsafe_get_score(self, contestant, num):
        """Loads a question score from database."""
        return pcm.JudgeScore.query.filter_by(
            judge_biv_id=flask.session['user.biv_id'],
            contestant_biv_id=contestant.biv_id,
            question_number=int(num)
        ).first()


class Nomination(flask_wtf.Form):
    """Plain form that accepts a website nomination.

    A 'Nominition' is created on form submission (see pcm.Nomination)
    If the website is new, then a 'Nominee' is added for that website.

    Fields: Website
    """

    website = wtforms.StringField(
        'Website url', validators=[
            wtfv.DataRequired(), wtfv.Length(max=200)])

    def execute(self, contest):
        """Validates website url and adds it to the database"""
        if self.is_submitted() and self.validate():
            nominee, _ = self._update_models(contest)
            url = nominee.url
            if url:
                flask.flash('Thank you for submitting {} to {}.'.format(url, contest.display_name))
                return flask.redirect(contest.format_uri('contestants'))
                # TODO(mda): Build the thank you page (currently I'm only
                # flashing a thank-you message on the contestants page
                return flask.redirect(contest.format_uri('thank-you-page'))
        return contest.task_class.render_template(
            contest,
            'nominate-website',
            form=self,
            selected='website-url'
        )

    def _update_models(self, contest):
        """Creates the Contestant and Founder models
        and adds BivAccess models to join the contest and Founder models"""
        url = self.website.data
        # (mda) get the time here to minimize server processing time
        # interference (just in case of a hangup of some sort)
        submission_datetime = self._get_current_time_MST()
        if not self._is_already_nominated(url):
            nominee = pcm.Nominee()
            self.populate_obj(nominee)
            nominee.url = url
            nominee.is_public = \
                ppc.app().config['PUBLICPRIZE']['ALL_PUBLIC_CONTESTANTS']
            nominee.is_under_review = False
            ppc.db.session.add(nominee)
            ppc.db.session.flush()
            ppc.db.session.add(
                pam.BivAccess(
                    source_biv_id=contest.biv_id,
                    target_biv_id=nominee.biv_id
                )
            )
        else:
            nominee = self._get_matching_nominee(url)
        assert nominee is not None
        nomination = pcm.Nomination()
        # TODO(mda): verify that the access route returns correct urls when
        # accessed from remote location (this is hard to test from a local
        # machine)
        route = flask.request.access_route
        # (mda) Trusting the first item in the client ip route is a potential
        # security risk, as the client may spoof this to potentially inject code
        # this shouldn't be a problem in our implementation, as in the worst
        # case, we'll just be recording a bogus value.
        try:
            nomination.client_ip = route[0][:pcm.Nomination.client_ip.type.length]
        except IndexError:
            nomination.client_ip = 'ip unrecordable'
            print("Error, failed to record client ip. route: {}. ".format(route),
                  "Recording ip as '{}'".format(nomination.client_ip),
                  file=sys.stderr)
        nomination.submission_datetime = submission_datetime
        nomination.nominee = nominee.biv_id
        ppc.db.session.add(nomination)
        ppc.db.session.flush()
        ppc.db.session.add(
            pam.BivAccess(
                source_biv_id=contest.biv_id,
                target_biv_id=nomination.biv_id
            )
        )
        return nominee, nomination

    def _is_already_nominated(self, url):
        return pcm.Nominee.query.filter(pcm.Nominee.url == url).count() > 0

    def _get_matching_nominee(self, url):
        return pcm.Nominee.query.filter(pcm.Nominee.url == url).first()

    def validate(self):
        """Performs url field validation"""
        self._validate_website()
        _log_errors(self)
        return not self.errors

    def _validate_website(self):
        """Ensures the website exists"""
        if self.website.errors:
            return
        if self.website.data:
            if not self._get_url_content(self.website.data):
                self.website.errors = ['Website invalid or unavailable.']

    def _get_current_time_MST(self):
        """Returns a datetime object with the current date in MST"""
        tz = pytz.timezone('US/Mountain')
        current_time = datetime.datetime.now(tz)
        return current_time

    def _get_url_content(self, url):
        """Performs a HTTP GET on the url.

        Returns False if the url is invalid or not-found"""
        res = None
        if not re.search(r'^http', url):
            url = 'http://' + url
        try:
            req = urllib.request.urlopen(url, None, 30)
            res = req.read().decode(locale.getlocale()[1])
            req.close()
        except urllib.request.URLError:
            return None
        except ValueError:
            return None
        except socket.timeout:
            return None
        return res

def _log_errors(form):
    """Put any form errors in logs as warning"""
    if form.errors:
        ppc.app().logger.warn({
            'data': flask.request.form,
            'errors': form.errors
        })
