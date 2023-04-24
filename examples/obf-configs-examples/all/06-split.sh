tigress \
  --Environment=x86_64:Linux:Gcc:4.6 \
  --Transform=Split \
    --SplitKinds=deep,block,top \
    --SplitCount=100 \
    --Functions=sort \
  --Transform=Split \
    --SplitKinds=block \
    --SplitCount=2 \
    --Functions=/.\*sort_split.\*/
