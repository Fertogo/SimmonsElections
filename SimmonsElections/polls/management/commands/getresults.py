from django.core.management.base import BaseCommand, CommandError
from polls.models import AnswerSet, Poll
import hashlib, time

class Command(BaseCommand):
    args = ''
    help = 'Get results from all polls'

    def hash(self, s, key):
        return chr(ord('A') + hash(s + key) % 26) + chr(ord('A') + hash(s + key + key) % 26)

    def get_vote(self, answer_set, active_votes):
        active_vote_num = active_votes[answer_set]
        if active_vote_num == 4:
            return None
        return answer_set.get_choice(active_vote_num)
    
    def handle(self, *args, **options):
        for poll in Poll.objects.all():
            key = str(time.time())
            self.stdout.write("===============================================\n")
            self.stdout.write("Results for Poll %s - %s\n" % (poll.id, poll.question))

            answer_sets = [answer_set for answer_set in AnswerSet.objects.all().filter(active=True, question=poll)]
            candidates = [candidate for candidate in poll.choice_set.all()]
            results = []

            active_votes = dict()
            for answer_set in answer_sets:
                active_votes[answer_set] = 1

            stage = 1
            reverse_ordering = []
            while len(candidates) > 0:
                votes = {}
                for candidate in candidates:
                    votes[candidate] = 0
                    
                for answer_set in answer_sets:
                    vote = self.get_vote(answer_set, active_votes)
                    if vote and vote in votes:
                        votes[vote] += 1

                # output votes
                self.stdout.write("  Stage %s\n" % stage)
                for candidate in sorted(candidates, key=lambda c: -votes[c]):
                    self.stdout.write("    %s: %d\n" % (self.hash(candidate.choice, key), votes[candidate]))

                # determine and eliminate last-place
                if len(candidates) == 1:
                    reverse_ordering.append(candidates[0])
                    self.stdout.write("    => %s wins!\n" % self.hash(candidates[0].choice, key))                    
                    self.stdout.write("\n")
                    break
                    
                min_votes = len(answer_sets) + 1 # MAX
                min_candidate = None
                for candidate in candidates:
                    if votes[candidate] < min_votes:
                        min_votes = votes[candidate]
                        min_candidate = candidate

                self.stdout.write("    => %s eliminated\n" % self.hash(min_candidate.choice, key))

                reverse_ordering.append(min_candidate)
                candidates.remove(min_candidate)
                # Reallocate votes
                transfer_votes = dict()
                for candidate in candidates:
                    transfer_votes[candidate] = 0
                transfer_votes[None] = 0
                
                for answer_set in answer_sets:
                    if self.get_vote(answer_set, active_votes) == min_candidate:
                        active_votes[answer_set] += 1
                        while self.get_vote(answer_set, active_votes) and self.get_vote(answer_set, active_votes) not in candidates:
                            active_votes[answer_set] += 1
                        transfer_votes[self.get_vote(answer_set, active_votes)] += 1
                for (transfer_cand, votes) in transfer_votes.iteritems():
                    name = self.hash(transfer_cand.choice, key) if transfer_cand else "None"
                    self.stdout.write("       -> %s: %d\n" % (name, votes))

                self.stdout.write("    \n")
                stage += 1

            ordering = reverse_ordering[::-1]
            self.stdout.write("  RESULTS:\n")
            for (i, winner) in enumerate(ordering):
                self.stdout.write("    %d. %s\n" % (i + 1, self.hash(winner.choice, key)))
            self.stdout.write("    \n")                                      
