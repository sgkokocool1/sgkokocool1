package solutions

func TwoSum(nums []int, target int) []int {
	seen := make(map[int]int)
	for i, x := range nums {
		if j, ok := seen[target-x]; ok {
			return []int{j, i}
		}
		seen[x] = i
	}
	return nil
}

func LongestConsecutive(nums []int) int {
	set := make(map[int]struct{}, len(nums))
	for _, x := range nums {
		set[x] = struct{}{}
	}
	best := 0
	for x := range set {
		if _, ok := set[x-1]; ok {
			continue
		}
		length := 1
		for {
			if _, ok := set[x+length]; !ok {
				break
			}
			length++
		}
		if length > best {
			best = length
		}
	}
	return best
}
