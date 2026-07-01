package solutions

func LengthOfLongestSubstring(s string) int {
	last := make(map[byte]int)
	left, maxLen := 0, 0
	for right := 0; right < len(s); right++ {
		c := s[right]
		if idx, ok := last[c]; ok && idx >= left {
			left = idx + 1
		}
		last[c] = right
		if right-left+1 > maxLen {
			maxLen = right - left + 1
		}
	}
	return maxLen
}

func SubarraySum(nums []int, k int) int {
	cnt := map[int]int{0: 1}
	pre, ans := 0, 0
	for _, x := range nums {
		pre += x
		ans += cnt[pre-k]
		cnt[pre]++
	}
	return ans
}
