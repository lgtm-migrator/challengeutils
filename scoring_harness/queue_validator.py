"""This is the baseclass for what happens to a submission"""
import logging
from .base_processor import EvaluationQueueProcessor
from . import messages

logging.basicConfig(format='%(asctime)s %(message)s')
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)


class EvaluationQueueValidator(EvaluationQueueProcessor):
    _success_status = "VALIDATED"

    def __init__(self, syn, evaluation, admin_user_ids=None, dry_run=False,
                 remove_cache=False, acknowledge_receipt=False,
                 send_messages=False, **kwargs):
        EvaluationQueueProcessor.__init__(self, syn, evaluation,
                                          admin_user_ids=admin_user_ids,
                                          dry_run=dry_run,
                                          remove_cache=remove_cache,
                                          **kwargs)
        self.acknowledge_receipt = acknowledge_receipt
        self.send_messages = send_messages

    def interaction_func(self, submission, **kwargs):
        raise NotImplementedError

    def notify(self, submission, submission_info):
        """Notify submitter or admin"""
        # send message AFTER storing status to ensure
        # we don't get repeat messages
        is_valid = submission_info['valid']
        error = submission_info['error']
        message = submission_info['message']

        participantid = submission.get("teamId")
        if participantid is not None:
            name = self.syn.getTeam(participantid)['name']
        else:
            participantid = submission.userId
            name = self.syn.getUserProfile(participantid)['userName']
        if is_valid:
            messages.validation_passed(syn=self.syn,
                                       userids=[participantid],
                                       acknowledge_receipt=self.acknowledge_receipt,  # noqa pylint: disable=line-too-long
                                       dry_run=self.dry_run,
                                       username=name,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
        else:
            if isinstance(error, AssertionError):
                send_to = [participantid]
                username = name
            else:
                send_to = self.admin_user_ids
                username = "Challenge Administrator"

            messages.validation_failed(syn=self.syn,
                                       userids=send_to,
                                       send_messages=self.send_messages,
                                       dry_run=self.dry_run,
                                       username=username,
                                       queue_name=self.evaluation.name,
                                       submission_id=submission.id,
                                       submission_name=submission.name,
                                       message=message,
                                       challenge_synid=self.evaluation.contentSource)  # noqa pylint: disable=line-too-long
