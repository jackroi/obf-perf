tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=Virtualize \
    --Functions=sort \
    --VirtualizeDispatch=direct \
  --Transform=JitDynamic \
    --Functions=sort \
    --JitDynamicCodecs=xtea \
    --JitDynamicBlockFraction=%20
