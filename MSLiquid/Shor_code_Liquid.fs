namespace Microsoft.Research.Liquid

module ShorCode =
  open System
  open Util
  open Operations
  open System
  
  let PrepareState (inputValue:int) (qs:Qubits) =
    if inputValue <> 0
      then X [qs.Head]
    H [qs.Head]

  let BitFlipEncode (idxs:List<int>) (qs:Qubits) =
    CNOT [qs.[idxs.[0]]; qs.[idxs.[1]]]
    CNOT [qs.[idxs.[0]]; qs.[idxs.[2]]]

  let PhaseFlipEncode (idxs:List<int>) (qs:Qubits) =
     BitFlipEncode idxs qs
     for idx in idxs do
       H [qs.[idx]]

  let ErrorIntroduction (idxs:List<int>) (qs:Qubits) =
    for idx in idxs do
      X [qs.[idx]]
      Z [qs.[idx]]
  
  let BitFlipDecode (idxs:List<int>) (qs:Qubits) =
    CNOT [qs.[idxs.[0]]; qs.[idxs.[1]]]
    CNOT [qs.[idxs.[0]]; qs.[idxs.[2]]]
    CCNOT [qs.[idxs.[1]]; qs.[idxs.[2]]; qs.[idxs.[0]]]

  let PhaseFlipDecode (idxs:List<int>) (qs:Qubits) =
    for idx in idxs do
      H [qs.[idx]]
    BitFlipDecode idxs qs
  
  let (|||||>) [a; b; c; d; e] func = func a b c d e

  let shorRun inputValue errorIdxs (qs:Qubits) =
    PrepareState inputValue qs

    PhaseFlipEncode [0; 3; 6] qs
    BitFlipEncode [0; 1; 2] qs
    BitFlipEncode [3; 4; 5] qs
    BitFlipEncode [6; 7; 8] qs

    ErrorIntroduction errorIdxs qs // Array.empty<int> qs

    BitFlipDecode [6; 7; 8] qs
    BitFlipDecode [3; 4; 5] qs
    BitFlipDecode [0; 1; 2] qs
    PhaseFlipDecode [0; 3; 6] qs

    H [qs.Head]

    M >< qs

  let rec decimalValueReversed (qs:Qubits) =
    if qs.IsEmpty then 0
    else qs.Head.Bit.v + 2 * decimalValueReversed qs.Tail

  let decimalValue (qs:Qubit List) =
    decimalValueReversed (List.rev qs)

  let rec comb n l = 
    match n, l with
    | 0, _ -> [[]]
    | _, [] -> []
    | k, (x::xs) -> List.map ((@) [x]) (comb (k-1) xs) @ comb k xs

  [<LQD>]
  let __ShorCode() =
    let nbqubits = 9
    let asExpected = true
    for inputValue in [0..1] do
      let errs = [0; 1; 2; 3; 4; 5; 6; 7; 8]
      for errorIdxs in comb 0 errs @ comb 1 errs do
        printf "Performing test for bit value %d with errors at positions " inputValue
        for errIdx in errorIdxs do
          printf "%d " errIdx
        printf "\n"
        let stats = Array.create 8 0
        let k = Ket(nbqubits)
        for i in 0..9 do // perform multiple runs
          let qs = k.Reset(nbqubits)
          shorRun inputValue errorIdxs qs
          if (inputValue = 0 && qs.[0].Bit.v = 0 || inputValue = 1 && qs.[0].Bit.v = 1) then
            ()
          else
            asExpected = false
            show "Unexpected result for input %d with %d bit flip errors, value of first bit is %d." inputValue errorIdxs.Length qs.[0].Bit.v
          stats.[qs.[0].Bit.v] <- stats.[qs.[0].Bit.v] + 1
        //show "Measured: 0=%d 1=%d 2=%d 3=%d 4=%d 5=%d 6=%d 7=%d" stats.[0] stats.[1] stats.[2] stats.[3] stats.[4] stats.[5] stats.[6] stats.[7]
    
    if asExpected then
      show "Success!"
    else
      show "One or more tests produced unexpected results."
module Main =
  open App
  [<EntryPoint>]
  let Main _ =
    RunLiquid ()