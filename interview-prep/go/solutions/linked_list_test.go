package solutions

import "testing"

func TestReverseList(t *testing.T) {
	head := &ListNode{1, &ListNode{2, &ListNode{3, nil}}}
	got := ReverseList(head)
	want := []int{3, 2, 1}
	for i, node := 0, got; i < len(want); i, node = i+1, node.Next {
		if node == nil || node.Val != want[i] {
			t.Fatalf("reverse failed at %d", i)
		}
	}
}

func TestDetectCycle(t *testing.T) {
	n1 := &ListNode{Val: 1}
	n2 := &ListNode{Val: 2}
	n3 := &ListNode{Val: 3}
	n1.Next = n2
	n2.Next = n3
	n3.Next = n2 // cycle at n2
	entry := DetectCycle(n1)
	if entry != n2 {
		t.Errorf("DetectCycle = %v, want node 2", entry)
	}
}
