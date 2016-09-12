import abc
from six import with_metaclass
from intervaltree import IntervalTree, Interval

class RLManager(with_metaclass(abc.ABCMeta)):

    def __init__(self, **kwargs):
        pass

    @abc.abstractmethod
    def get_restrictions(self, start, end):
        raise NotImplementedError

    @abc.abstractmethod
    def restriction(self, sid, dt):
        raise NotImplementedError

    @abc.abstractmethod
    def is_restricted(self, sid, dt):
        raise NotImplementedError


class InMemoryRLManager(RLManager):

    def __init__(self, restrictions):
        super(InMemoryRLManager, self).__init__()
        self.restrictions = restrictions
        self.restriction_history = {}

    def get_restrictions(self, start, end):
        for sid, restrictions in self.restriction_history:
            intervals = []
            for i, restriction in enumerate(restrictions):
                if restriction.effective_date < start:
                    continue
                try:
                    interval_end = restrictions[i+1].effective_date
                except IndexError:
                    interval_end = end
                intervals.append(Interval(restriction.effective_date,
                                          interval_end,
                                          restriction.restriction_type))
            self.restriction_history[sid] = IntervalTree(intervals)

    def restriction(self, sid, dt):
        try:
            restrictions_for_sid = self.restriction_history[sid]
        except KeyError:
            return 'allowed'

        return list(restrictions_for_sid[dt])[0].data

    def is_restricted(self, sid, dt):
        return self.restriction(sid, dt) != 'allowed'
