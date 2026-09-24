--!strict
-- Allows at most `limit` requests per player per `window` seconds (fixed windows).

export type RateLimiter = {
	Limit: number,
	Window: number,
	Buckets: { [Player]: { Count: number, WindowStart: number } },
}

local RateLimiter = {}

function RateLimiter.New(limit: number, window: number): RateLimiter
	return { Limit = limit, Window = window, Buckets = {} }
end

function RateLimiter.Allow(limiter: RateLimiter, player: Player): boolean
	local now = os.clock()
	local bucket = limiter.Buckets[player]
	if not bucket or now - bucket.WindowStart >= limiter.Window then
		limiter.Buckets[player] = { Count = 1, WindowStart = now }
		return true
	end
	if bucket.Count >= limiter.Limit then
		return false
	end
	bucket.Count += 1
	return true
end

-- Call on PlayerRemoving so the table doesn't keep old players alive.
function RateLimiter.Remove(limiter: RateLimiter, player: Player)
	limiter.Buckets[player] = nil
end

return RateLimiter
