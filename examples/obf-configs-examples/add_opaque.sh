# TODO: fix: segmentation fault

tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
   --Inputs="+1:int:42,-1:length:1?10" \
   --Transform=InitImplicitFlow \
      --Functions=main \
   --Transform=InitEntropy \
   --Transform=InitOpaque \
      --Functions=main \
      --InitOpaqueCount=2 \
      --InitOpaqueStructs=list,array,input,env \
   --Transform=AddOpaque \
      --Functions=* \
      --AddOpaqueKinds=question \
      --AddOpaqueSplitKinds=inside \
      --AddOpaqueCount=3
