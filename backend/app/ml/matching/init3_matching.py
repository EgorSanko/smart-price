"""Product matching for cross-marketplace entity resolution."""

from app.ml.matching.matcher import ProductMatcher, MatchResult, get_product_matcher

__all__ = ["ProductMatcher", "MatchResult", "get_product_matcher"]
