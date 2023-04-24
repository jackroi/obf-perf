tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=InitEntropy \
  --Transform=InitOpaque \
    --Functions=main \
  --Transform=AntiBranchAnalysis \
    --Functions=sort \
    --AntiBranchAnalysisKinds=goto2nopSled
