import abc
from six import with_metaclass
from intervaltree import IntervalTree, Interval


class RestrictionsController(object):

    def __init__(self):
        self.rl_managers = []

    def add_restrictions(self, rl_manager):
        self.rl_managers.append(rl_manager)

    def restriction(self, sid, dt):
        restrictions = [rlm.restriction(sid, dt) for rlm in self.rl_managers]
        if 'liquidate' in restrictions:
            return 'liquidate'
        elif 'freeze' in restrictions:
            return 'freeze'
        elif 'long_only' in restrictions and 'reduce_only' in restrictions:
            return 'freeze'
        elif 'long_only' in restrictions:
            return 'long_only'
        elif 'reduce_only' in restrictions:
            return 'reduce_only'
        else:
            return 'allowed'

    def is_restricted(self, sid, dt):
        return any([rlm.is_restricted(sid, dt) for rlm in self.rl_managers])


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
