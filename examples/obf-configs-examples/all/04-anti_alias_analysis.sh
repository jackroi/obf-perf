tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=InitEntropy \
  --Transform=InitOpaque \
    --Functions=main \
    --InitOpaqueCount=2 \
    --InitOpaqueStructs=list,array,input,env \
  --Transform=AntiAliasAnalysis \
    --Functions=sort

