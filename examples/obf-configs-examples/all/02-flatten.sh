tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=Flatten \
    --Functions=* \
    --FlattenDispatch=switch \
    --FlattenObfuscateNext=false \
    --FlattenRandomizeBlocks=true \
    --FlattenConditionalKinds=branch,compute,flag \
    --FlattenImplicitFlowNext=true
