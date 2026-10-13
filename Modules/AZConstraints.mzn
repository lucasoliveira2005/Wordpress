/*
 * Ensures that at most 1 replica of a component is placed per Availability Zone.
 */
predicate az_dispersion(array[int, int] of var 0..1: AssignmentMatrix,
                        array[int] of int: VMZone,
                        int: NoZones,
                        int: VM,
                        int: compID) =
    forall(z in 1..NoZones)(
        sum(k in 1..VM where VMZone[k] == z)(AssignmentMatrix[compID, k]) <= 1
    );
