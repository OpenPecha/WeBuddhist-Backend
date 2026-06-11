from pecha_api.daily_log.daily_log_response_models import UserStreakResponse


def test_user_streak_response_model():
    response = UserStreakResponse(streak=7)

    assert response.streak == 7
    assert response.model_dump() == {"streak": 7}
