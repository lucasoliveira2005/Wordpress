predicate az_dispersion(array[int, int] of var 0..1: AssignmentMatrix,
                        array[int] of var int: VMZone,
                        int: NoZones,
                        int: VM,
                        int: compID) =
    forall(k1 in 1..VM, k2 in k1+1..VM)(
        (AssignmentMatrix[compID, k1] + AssignmentMatrix[compID, k2] == 2) ->
            (VMZone[k1] != VMZone[k2])
    );


predicate latency_sla(array[int, int] of var 0..1: AssignmentMatrix,
                      array[int] of var int: VMZone,
                      array[int, int] of int: ZoneLatency,
                      int: MaxAllowedLatency,
                      int: VM,
                      int: comp1,
                      int: comp2) =
    forall(z1 in 1..NoZones, z2 in 1..NoZones where ZoneLatency[z1, z2] > MaxAllowedLatency)(
        forall(k1 in 1..VM, k2 in 1..VM)(
            (VMZone[k1] == z1 /\ VMZone[k2] == z2) ->
                (AssignmentMatrix[comp1, k1] + AssignmentMatrix[comp2, k2] <= 1)
        )
    );
