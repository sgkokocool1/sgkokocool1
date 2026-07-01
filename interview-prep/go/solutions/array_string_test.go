package solutions

import "testing"

func TestLengthOfLongestSubstring(t *testing.T) {
	tests := []struct {
		s    string
		want int
	}{
		{"abcabcbb", 3},
		{"bbbbb", 1},
		{"pwwkew", 3},
		{"", 0},
	}
	for _, tt := range tests {
		if got := LengthOfLongestSubstring(tt.s); got != tt.want {
			t.Errorf("LengthOfLongestSubstring(%q) = %d, want %d", tt.s, got, tt.want)
		}
	}
}

func TestSubarraySum(t *testing.T) {
	if got := SubarraySum([]int{1, 1, 1}, 2); got != 2 {
		t.Errorf("SubarraySum = %d, want 2", got)
	}
	if got := SubarraySum([]int{1, 2, 3}, 3); got != 2 {
		t.Errorf("SubarraySum = %d, want 2", got)
	}
}
