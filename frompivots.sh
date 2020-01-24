SENT1="That even the powers of time can be altered for a single purpose?"
SENT2="Nothing is so painful to the human mind as a great and sudden change."


### Generate for source sentences and pivot sentences

P11="That is one of the things that we learn in an asylum, at any rate."
P12="My father died in the Lazaretto, more through grief than disease."
P21="Whether I am ill, or well, nothing will induce me to lose sight of her."
P22="Do you mind ringing for Louis to carry the portfolio to your own room?"

# 1. Get features for source and pivot strings
POSTDATA="{\"sources\": [\"$SENT1\", \"$SENT2\"], \"pivots\": [[\"$P11\", \"$P12\"],[\"$P21\",\"$P22\"]]}" 

PIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$POSTDATA" \
    http://localhost:5000/styleeq/api/v1.0/getpivots)

echo "### PIVOT FEATURES ###"
echo "$PIVOTS"

# 2. Generate from source and pivot features
FROMPIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$PIVOTS" \
    http://localhost:5000/styleeq/api/v1.0/frompivots)

echo "### GENERATION FROM PIVOTS ###"
echo "$FROMPIVOTS"



