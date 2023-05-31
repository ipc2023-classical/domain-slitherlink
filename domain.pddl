(define (domain slitherlink)
(:requirements :typing :adl)

(:types
    node - object
    cell - object
    cell-capacity-level - object
)

(:predicates
    ;; Ordering of cell capacities
    (cell-capacity-inc ?clower ?chigher - cell-capacity-level)
    ;; Current cell capacity, i.e., how many links can be placed around the cell
    (cell-capacity ?c - cell ?cap - cell-capacity-level)
    ;; The node (vertex) is not connected to any link
    (node-degree0 ?n - node)
    ;; The node is connected to exactly one link
    (node-degree1 ?n - node)
    ;; The node is connected to exactly two links
    (node-degree2 ?n - node)
    ;; The edge between nodes ?n1 ?n2 is an edge the cells ?c1 and ?c2
    (cell-edge ?c1 ?c2 - cell ?n1 ?n2 - node)
    ;; ?n1 and ?n2 are (slither)linked
    (linked ?n1 ?n2 - node)
    ;; Disables link-0-0 action after its first use
    (disable-link-0-0)
)

;; This action is used only at the beginning of a plan. Disabling it (using
;; the predicate disable-link-0-0) after its first use ensures that the
;; solution is a single cycle.
;; Without it, the plan could produce several closed loops. For example:
;; input:      possible incorrect solution:     correct solution:
;; + + + +                +-+ + +                   +-+-+-+
;;  3 . .                 |3|. .                    |3 . .|
;; + + + +                + + +-+                   +-+ +-+
;;  . . 3                 |.|.|3|                    .|.|3 
;; + + + +                +-+ + +                   +-+ +-+
;;  . 1 3                  . 1|3|                   |. 1 3|
;; + + + +                + + +-+                   +-+-+-+
;;
;; Another possibility would be to remove this action entirely and put one or
;; more starting links in the initial state.
(:action link-0-0
    :parameters (?n1 - node ?n2 - node
                 ?c1 - cell ?c1capfrom ?c1capto - cell-capacity-level
                 ?c2 - cell ?c2capfrom ?c2capto - cell-capacity-level)
    :precondition
        (and
            (not (linked ?n1 ?n2))
            (node-degree0 ?n1)
            (node-degree0 ?n2)
            (cell-edge ?c1 ?c2 ?n1 ?n2)
            (cell-capacity ?c1 ?c1capfrom)
            (cell-capacity ?c2 ?c2capfrom)
            (cell-capacity-inc ?c1capto ?c1capfrom)
            (cell-capacity-inc ?c2capto ?c2capfrom)
            (not (disable-link-0-0))
        )
    :effect
        (and
            (linked ?n1 ?n2)

            (not (node-degree0 ?n1))
            (node-degree1 ?n1)

            (not (node-degree0 ?n2))
            (node-degree1 ?n2)

            (not (cell-capacity ?c1 ?c1capfrom))
            (cell-capacity ?c1 ?c1capto)

            (not (cell-capacity ?c2 ?c2capfrom))
            (cell-capacity ?c2 ?c2capto)

            (disable-link-0-0)
        )
)

(:action link-0-1
    :parameters (?n1 - node ?n2 - node
                 ?c1 - cell ?c1capfrom ?c1capto - cell-capacity-level
                 ?c2 - cell ?c2capfrom ?c2capto - cell-capacity-level)
    :precondition
        (and
            (not (linked ?n1 ?n2))
            (node-degree0 ?n1)
            (node-degree1 ?n2)
            (cell-edge ?c1 ?c2 ?n1 ?n2)
            (cell-capacity ?c1 ?c1capfrom)
            (cell-capacity ?c2 ?c2capfrom)
            (cell-capacity-inc ?c1capto ?c1capfrom)
            (cell-capacity-inc ?c2capto ?c2capfrom)
        )
    :effect
        (and
            (linked ?n1 ?n2)

            (not (node-degree0 ?n1))
            (node-degree1 ?n1)

            (not (node-degree1 ?n2))
            (node-degree2 ?n2)

            (not (cell-capacity ?c1 ?c1capfrom))
            (cell-capacity ?c1 ?c1capto)

            (not (cell-capacity ?c2 ?c2capfrom))
            (cell-capacity ?c2 ?c2capto)
        )
)

(:action link-1-0
    :parameters (?n1 - node ?n2 - node
                 ?c1 - cell ?c1capfrom ?c1capto - cell-capacity-level
                 ?c2 - cell ?c2capfrom ?c2capto - cell-capacity-level)
    :precondition
        (and
            (not (linked ?n1 ?n2))
            (node-degree1 ?n1)
            (node-degree0 ?n2)
            (cell-edge ?c1 ?c2 ?n1 ?n2)
            (cell-capacity ?c1 ?c1capfrom)
            (cell-capacity ?c2 ?c2capfrom)
            (cell-capacity-inc ?c1capto ?c1capfrom)
            (cell-capacity-inc ?c2capto ?c2capfrom)
        )
    :effect
        (and
            (linked ?n1 ?n2)

            (not (node-degree1 ?n1))
            (node-degree2 ?n1)

            (not (node-degree0 ?n2))
            (node-degree1 ?n2)

            (not (cell-capacity ?c1 ?c1capfrom))
            (cell-capacity ?c1 ?c1capto)

            (not (cell-capacity ?c2 ?c2capfrom))
            (cell-capacity ?c2 ?c2capto)
        )
)

(:action link-1-1
    :parameters (?n1 - node ?n2 - node
                 ?c1 - cell ?c1capfrom ?c1capto - cell-capacity-level
                 ?c2 - cell ?c2capfrom ?c2capto - cell-capacity-level)
    :precondition
        (and
            (not (linked ?n1 ?n2))
            (node-degree1 ?n1)
            (node-degree1 ?n2)
            (cell-edge ?c1 ?c2 ?n1 ?n2)
            (cell-capacity ?c1 ?c1capfrom)
            (cell-capacity ?c2 ?c2capfrom)
            (cell-capacity-inc ?c1capto ?c1capfrom)
            (cell-capacity-inc ?c2capto ?c2capfrom)
        )
    :effect
        (and
            (linked ?n1 ?n2)

            (not (node-degree1 ?n1))
            (node-degree2 ?n1)

            (not (node-degree1 ?n2))
            (node-degree2 ?n2)

            (not (cell-capacity ?c1 ?c1capfrom))
            (cell-capacity ?c1 ?c1capto)

            (not (cell-capacity ?c2 ?c2capfrom))
            (cell-capacity ?c2 ?c2capto)
        )
)
)
