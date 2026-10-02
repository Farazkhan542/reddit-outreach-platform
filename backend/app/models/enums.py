import enum


class Role(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class ApprovalMode(str, enum.Enum):
    # Every draft needs human approval; kept as an enum so the setting is explicit.
    manual = "manual"


class LeadStatus(str, enum.Enum):
    new = "new"
    qualified = "qualified"
    disqualified = "disqualified"
    assigned = "assigned"
    contacted = "contacted"
    converted = "converted"


class ReplyStatus(str, enum.Enum):
    pending_review = "pending_review"
    approved = "approved"  # ready for the reviewer to post manually on reddit.com
    rejected = "rejected"
    posted = "posted"  # reviewer confirmed they posted it themselves


class DistributionStrategy(str, enum.Enum):
    round_robin = "round_robin"
    least_recently_active = "least_recently_active"
    manual_claim = "manual_claim"
