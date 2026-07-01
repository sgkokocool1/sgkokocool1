package solutions

import (
	"reflect"
	"testing"
)

func TestTwoSum(t *testing.T) {
	got := TwoSum([]int{2, 7, 11, 15}, 9)
	want := []int{0, 1}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("TwoSum = %v, want %v", got, want)
	}
}

func TestLongestConsecutive(t *testing.T) {
	got := LongestConsecutive([]int{100, 4, 200, 1, 3, 2})
	if got != 4 {
		t.Errorf("LongestConsecutive = %d, want 4", got)
	}
}
