SENT1="My Corvette died in the Lazaretto, more through grief than disease."
SENT2="Do you mind ringing for Louis to carry the portfolio to your own room?"


P11="That is one of the things that we learn in an asylum, at any rate."
P12="That even the powers of time can be altered for a single purpose?"
P21="Whether I am ill, or well, nothing will induce me to lose sight of her."
P22="Nothing is so painful to the human mind as a great and sudden change."

# 1. Get features for source and pivot strings
POSTDATA="{\"sources\": [\"$SENT1\", \"$SENT2\"], \"pivots\": [[\"$P11\", \"$P12\"],[\"$P21\",\"$P22\"]]}" 

PIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$POSTDATA" \
    http://localhost:5000/styleeq/api/v1.0/getpivots)

# 2. Generate from source and pivot features
FROMPIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$PIVOTS" \
    http://localhost:5000/styleeq/api/v1.0/frompivots)

echo "### GENERATION FROM PIVOTS ###"
echo "$FROMPIVOTS"


SOURCES="[\"$SENT1\", \"$SENT2\"]"
#GENRE="\"scifi\""
#GENRE="\"philosophy\""
GENRE="\"gothic\""

# 1. Get pivot features for gothic corpus, num_pivots determines the number
#    of pivots to retrieve. sources is a list of sentences to get pivots for. 
#    Returns {"sources": [list of source strings], 
#             "features": [list of features for each source sentence],
#             "pivots": [list of lists of num_pivot pivot features]}

POSTDATA="{\"sources\": $SOURCES, \"genre\": $GENRE, \"num_pivots\": 2}"
PIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$POSTDATA" \
    http://localhost:5000/styleeq/api/v1.0/getpivots)

FROMPIVOTS=$(curl -s -H "Content-Type: application/json" -X POST -d "$PIVOTS" \
    http://localhost:5000/styleeq/api/v1.0/frompivots)
echo "### GENERATION FROM PIVOTS ###"
echo "$FROMPIVOTS"


FEATS=$(curl -s -H "Content-Type: application/json" -X POST \
    -d "{\"sources\": [\"$SENT1\", \"$SENT2\"]}" \
    http://localhost:5000/styleeq/api/v1.0/getfeatures)

# 2. Generate from  features
FROMFEATS=$(curl -s -H "Content-Type: application/json" -X POST -d "$FEATS" \
    http://localhost:5000/styleeq/api/v1.0/fromfeatures)

echo "### GENERATION FROM FEATURES ###"
echo "$FROMFEATS"




