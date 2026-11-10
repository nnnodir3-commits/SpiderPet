"""State model for the SpiderPet silk retreat. Pure Python for deterministic tests."""
import math

class RetreatLifecycle:
    """An owner-linked shelter that remains while occupied or intermittently reused.

    The age clock starts only when the spider exits the shelter's vicinity.
    On re-entry the clock and any partial fading are cancelled. After 300 s
    outside, transparency decreases linearly over the next 30 s. A fully
    expired shelter is removed before a new one may be planned.
    """
    def __init__(self, abandon_after=300., fade_seconds=30., vicinity_radius=75.):
        self.abandon_after=max(.1,float(abandon_after))
        self.fade_seconds=max(.1,float(fade_seconds))
        self.vicinity_radius=max(1.,float(vicinity_radius))
        self.position=None
        self.status='none'
        self.left_at=None

    @property
    def exists(self):
        return self.position is not None

    @property
    def completed(self):
        return self.status in ('ready','fading')

    def plan(self,position):
        if self.exists:
            raise ValueError('Existing shelter must be reused or expired')
        self.position=(float(position[0]),float(position[1]))
        self.status='planned'
        self.left_at=None

    def start_build(self):
        if not self.exists:
            raise ValueError('No shelter site planned')
        if self.status=='planned':
            self.status='building'
        elif self.status!='building':
            raise ValueError('Existing completed shelter cannot be rebuilt')

    def finish(self,now):
        if self.status!='building':
            raise ValueError('Cannot finish an unstarted shelter')
        self.status='ready'
        self.left_at=None

    def returned(self,now):
        if self.completed:
            self.status='ready'
            self.left_at=None

    def clear(self):
        self.position=None
        self.status='none'
        self.left_at=None

    def update(self,now,spider_position):
        """Return visible alpha 0..1; automatically discard expired retreat."""
        if not self.completed:
            return 1.
        if math.hypot(spider_position[0]-self.position[0],
                      spider_position[1]-self.position[1])<=self.vicinity_radius:
            self.returned(now)
            return 1.
        if self.left_at is None:
            self.left_at=now
        elapsed=max(0.,now-self.left_at)
        if elapsed<self.abandon_after:
            self.status='ready'
            return 1.
        self.status='fading'
        alpha=max(0.,1.-(elapsed-self.abandon_after)/self.fade_seconds)
        if alpha<=0:
            self.clear()
            return 0.
        return alpha
