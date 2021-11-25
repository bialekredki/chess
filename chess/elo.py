

def expected_score(player_elo:int, opponent_elo:int)->float:
    return 1/( 10**( ( player_elo-opponent_elo ) / 400) +  1 )

def k_factor(player_elo:int, rapid:bool, games_number:int) -> int:
    if rapid or player_elo < 2400: return 20
    if games_number <= 30: return 40
    return 10

