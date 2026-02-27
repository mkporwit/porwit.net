"""Tests for models.py - deck creation, challenge mapping, week calculation."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from models import (
    create_deck,
    get_challenge,
    get_current_week,
    create_new_deck_for_user,
    card_with_challenge,
    SUITS,
    RANKS,
)


class TestCreateDeck:
    def test_deck_has_54_cards(self):
        deck = create_deck()
        assert len(deck) == 54

    def test_deck_has_52_standard_cards(self):
        deck = create_deck()
        standard = [c for c in deck if c["rank"] != "JOKER"]
        assert len(standard) == 52

    def test_deck_has_2_jokers(self):
        deck = create_deck()
        jokers = [c for c in deck if c["rank"] == "JOKER"]
        assert len(jokers) == 2
        suits = {j["suit"] for j in jokers}
        assert suits == {"Red", "Black"}

    def test_deck_has_all_suit_rank_combinations(self):
        deck = create_deck()
        standard = {(c["rank"], c["suit"]) for c in deck if c["rank"] != "JOKER"}
        expected = {(r, s) for s in SUITS for r in RANKS}
        assert standard == expected

    def test_each_card_has_rank_and_suit(self):
        deck = create_deck()
        for card in deck:
            assert "rank" in card
            assert "suit" in card


class TestGetChallenge:
    def test_joker(self):
        result = get_challenge("JOKER")
        assert "20 yards" in result
        assert "20 seconds" in result

    def test_ace(self):
        result = get_challenge("A")
        assert "11 yards" in result
        assert "11 seconds" in result

    def test_face_cards(self):
        for rank in ["J", "Q", "K"]:
            result = get_challenge(rank)
            assert "15 yards" in result
            assert "15 seconds" in result

    def test_number_cards(self):
        for rank in ["2", "3", "4", "5", "6", "7", "8", "9", "10"]:
            result = get_challenge(rank)
            assert f"{rank} yards" in result
            assert f"{rank} seconds" in result

    def test_all_challenges_mention_5_shots(self):
        all_ranks = RANKS + ["JOKER"]
        for rank in all_ranks:
            assert "5 shots" in get_challenge(rank)


class TestGetCurrentWeek:
    def test_returns_tuple_of_two_ints(self):
        year, week = get_current_week()
        assert isinstance(year, int)
        assert isinstance(week, int)

    def test_year_is_reasonable(self):
        year, _ = get_current_week()
        assert 2024 <= year <= 2100

    def test_week_is_valid_iso_range(self):
        _, week = get_current_week()
        assert 1 <= week <= 53


class TestCreateNewDeckForUser:
    def test_deck_has_required_fields(self):
        deck = create_new_deck_for_user("test@example.com")
        assert "pk" in deck
        assert "sk" in deck
        assert "deck_id" in deck
        assert "email" in deck
        assert "shuffled_cards" in deck
        assert "cards_drawn" in deck
        assert "draw_history" in deck
        assert "created_at" in deck
        assert "completed_at" in deck

    def test_deck_pk_format(self):
        deck = create_new_deck_for_user("test@example.com")
        assert deck["pk"].startswith("DECK#")

    def test_deck_sk_format(self):
        deck = create_new_deck_for_user("test@example.com")
        assert deck["sk"] == "USER#test@example.com"

    def test_deck_starts_empty(self):
        deck = create_new_deck_for_user("test@example.com")
        assert deck["cards_drawn"] == 0
        assert deck["draw_history"] == []
        assert deck["completed_at"] is None

    def test_deck_has_54_shuffled_cards(self):
        deck = create_new_deck_for_user("test@example.com")
        assert len(deck["shuffled_cards"]) == 54

    def test_deck_is_shuffled(self):
        """Two decks should almost certainly have different orderings."""
        deck1 = create_new_deck_for_user("test@example.com")
        deck2 = create_new_deck_for_user("test@example.com")
        # Compare card orderings - extremely unlikely to be identical
        cards1 = [(c["rank"], c["suit"]) for c in deck1["shuffled_cards"]]
        cards2 = [(c["rank"], c["suit"]) for c in deck2["shuffled_cards"]]
        assert cards1 != cards2

    def test_different_decks_get_different_ids(self):
        deck1 = create_new_deck_for_user("test@example.com")
        deck2 = create_new_deck_for_user("test@example.com")
        assert deck1["deck_id"] != deck2["deck_id"]


class TestCardWithChallenge:
    def test_adds_challenge_field(self):
        card = {"rank": "7", "suit": "Hearts"}
        result = card_with_challenge(card)
        assert "challenge" in result

    def test_preserves_original_fields(self):
        card = {"rank": "7", "suit": "Hearts"}
        result = card_with_challenge(card)
        assert result["rank"] == "7"
        assert result["suit"] == "Hearts"

    def test_challenge_matches_get_challenge(self):
        card = {"rank": "A", "suit": "Spades"}
        result = card_with_challenge(card)
        assert result["challenge"] == get_challenge("A")

    def test_does_not_mutate_original(self):
        card = {"rank": "7", "suit": "Hearts"}
        card_with_challenge(card)
        assert "challenge" not in card
