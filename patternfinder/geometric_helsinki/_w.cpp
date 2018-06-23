#include<stdio.h>
#include<string.h>

#include <nlohmann/json.hpp>

#include <fstream>
#include <iostream>
#include <vector>
#include <string> // std::stof, std::stoi
#include <map>
#include <algorithm> //sort
#include <queue>

using namespace std;

using namespace nlohmann;

class IntraVector {

public:
    IntraVector(const char* csvLine);
    void print();
    float x;
    int y;
    int startIndex;
    int endIndex;
};

IntraVector::IntraVector(const char* csvLine){

    // Parse CSV line
    vector<string> res;
    do {
        const char* ptr = csvLine;
        while(*csvLine != ',' && *csvLine){
            csvLine++;
        }
        res.push_back(string(ptr, csvLine));
    } while(0 != *csvLine++);

    // Extract data according to schema
    x = stof(res[0]);
    y = stoi(res[1]);
    startIndex = stoi(res[2]);
    endIndex = stoi(res[3]);
}

void IntraVector::print() {
    printf("x %f; y %d; start %d; end %d;", x, y, startIndex, endIndex);
}

bool sortVectorsByStartIndex(IntraVector i, IntraVector j) {
    return i.startIndex < j.startIndex;
}

class KEntry {

public:
    KEntry(IntraVector& a, IntraVector& b) : 
        patternVec(a),
        targetVec(b) {}
    void print();
    IntraVector patternVec;
    IntraVector targetVec;
    float scale;
    int w = 0; // length of occurrence
    int id = 0;
    int e;
    KEntry* y = nullptr; // backlink for building chains
};

void KEntry::print(){
    printf("PatternVec: \n");
    patternVec.print();
    printf("TargetVec: \n");
    targetVec.print();
};

struct orderKEntriesByEndIndex{
    // PQueue takes a _Compare class for > operator
    bool operator()(const KEntry& left, const KEntry& right){
        if (left.targetVec.endIndex == right.targetVec.endIndex){
            return left.targetVec.startIndex > right.targetVec.startIndex;
        }
        return left.targetVec.endIndex > right.targetVec.endIndex;
    }
};

bool sortKEntriesByStartIndex(KEntry i, KEntry j){
    // Sort() takes a comparator function for < operator
    if (i.targetVec.startIndex == j.targetVec.startIndex){
        return i.targetVec.endIndex < j.targetVec.endIndex;
    }
    return i.targetVec.startIndex < j.targetVec.startIndex;
}

//KEntry::KEntry(IntraVector& a, IntraVector& b) : patternVec(a), targetVec(b){
//};

class Score {

public:
    Score(char* filePath);
    void printVectors();
    int numNotes;
    vector<IntraVector> vectors;
    map<int, vector<IntraVector>> hashedVectorsToY;
    map<int, vector<IntraVector>> hashedVectorsToStartIndex;
};

Score::Score(char* filePath) {
    string line;
    ifstream input;
    input.open(filePath);

    //Skip first line, which defines CSV headers
    input >> line;

    //Second line denots number of notes in the score
    input >> line;
    numNotes = stoi(line);

    // Third line is the number of intra vectors
    input >> line;
    int numVectors = stoi(line);

    //Every subsequent line is an intra vector CSV entry
    for (int i=0; i<numVectors; i++){
        input >> line;
        const char* c = line.c_str();
        IntraVector vec (c);
        vectors.push_back(vec);
        hashedVectorsToY[vec.y].push_back(vec);
        hashedVectorsToStartIndex[vec.startIndex].push_back(vec);
    }

    input.close();
};

void Score::printVectors() {
    printf("%lu vectors\n", vectors.size());
    for (int i=0; i < vectors.size(); i++){
        vectors[i].print();
        printf("\n");
    }
};

void printKTables(vector<KEntry>* KTables, int length){
    for (int i=0; i < length; i++){
        printf("========================\n");
        printf("====== KTable %d =======\n", i);
        printf("========================\n");
        for (int j=0; j < KTables[i].size(); j++){
            printf("patternvec: ");
            KTables[i][j].patternVec.print();
            printf("    targetvec: ");
            KTables[i][j].targetVec.print();
            printf("\n");
        }
    }
}


void fillKTables(vector<KEntry>* KTables, Score pattern, Score target){

    // There are m-1 KTables, one for each pattern IntraVector
    for (int i=0; i < pattern.numNotes - 1; i++){
        // For all pattern vectors which start at this pattern note
        for (int j=0; j < pattern.hashedVectorsToStartIndex[i].size(); j++){
            IntraVector curPatternVec = pattern.hashedVectorsToStartIndex[i][j];

            // Make a new entry with all target vectors that have the same Y coordinate
            for (int k=0; k < target.hashedVectorsToY[curPatternVec.y].size(); k++){
                IntraVector curTargetVec = target.hashedVectorsToY[curPatternVec.y][k];

                KEntry newEntry (curPatternVec, curTargetVec);
                KTables[i].push_back(newEntry);
            }
        }
        sort(KTables[i].begin(), KTables[i].end(), sortKEntriesByStartIndex);
    }
}

void algorithm(vector <KEntry>* KTables, Score pattern, Score target){
    
    priority_queue<KEntry, vector<KEntry>, orderKEntriesByEndIndex> queues[pattern.numNotes];
    int occId = 1; // Occurrence id

    // PQs hold chains which end at pattern note i
    // We intend to extend them with entries in a subsequent KTable
    // Initialize the first PQ
    for (int i=0; i < pattern.numNotes - 2; i++){
        for (int j=0; j < KTables[i].size(); j++){
            queues[KTables[i][j].patternVec.endIndex].push(KTables[i][j]);
        }
    }

    // For all K tables except the first (already copied to queue) (there are m - 1 Ktables)
    for (int i=1; i <= pattern.numNotes - 2; i++){
        KEntry q = queues[i].top();
        queues[i].pop();
        
        // For all rows in the current K Table
        for (int j=0; j < KTables[i].size(); j++){
            // Advance the possible antecedent until it matches our first postcedent
            while (q.targetVec.endIndex < KTables[i][j].targetVec.startIndex && !queues[i].empty()){
                q = queues[i].top();
                queues[i].pop();
            }

            if (q.targetVec.endIndex == KTables[i][j].targetVec.startIndex){
                // For multiple possible antecedents (multiple chains), take the longest one
                while (queues[i].top().targetVec.endIndex == q.targetVec.endIndex && !queues[i].empty()){
                    KEntry r = queues[i].top();
                    queues[i].pop();
                    if (r.w >= q.w){
                        q = r;
                    }
                }
                // Binding of Extension
                if (KTables[i][j].id == 0) {
                    KTables[i][j].id = occId++;
                }
                KTables[i][j].w = q.w + 1;
                KTables[i][j].y = (KEntry*) malloc(sizeof(KEntry));
                memcpy(KTables[i][j].y, &q, sizeof(KEntry));
                queues[KTables[i][j].patternVec.endIndex].push(KTables[i][j]);
            }
        }
        KTables[i][KTables[i].size() - 1].e = 1;
        queues[i+1].push(KTables[i][KTables[i].size() - 1]);
    }
}

void extractChain(KEntry row, vector<pair<int, int>> &chain) {
    if (row.y == nullptr) {
        pair<int, int> first (row.patternVec.startIndex, row.targetVec.startIndex);
        chain.push_back(first);
    }
    else {
        pair<int, int> matchingPair (row.patternVec.startIndex, row.targetVec.startIndex);
        chain.push_back(matchingPair);
        // Recurse on the backlink
        extractChain(*(row.y), chain);
    }
}

pair<int, int> getMaxWindowsFromChain(vector<pair<int, int>> chain){
    int maxPattern = 0;
    int maxTarget = 0;
    for (int i=1; i < chain.size(); i++){
        int newPatternDiff = chain[i].first - chain[i-1].first;
        int newTargetDiff = chain[i].first - chain[i-1].second;
        if (newPatternDiff > maxPattern){
            maxPattern = newPatternDiff;
        }
        if (newTargetDiff > maxTarget){
            maxTarget = newTargetDiff;
        }
    }
    pair<int,int> res (maxPattern, maxTarget); 
    return res;
}

vector<int> filterVectorPairForSecond(vector<pair<int, int>> p){
    vector<int> res;
    for (int i=0; i < p.size(); i++){
        res.push_back(p[i].second);
    }
    return res;
}


void writeChainsToJson(vector<KEntry>* KTables, Score pattern, Score target, string file_path) {
    map<int, vector<pair<int, int>>> chains;
    
    // Inspect all KTables
    for (int i=0; i < pattern.numNotes - 1; i++){
        for (int j=0; j<KTables[i].size(); j++){
            // The size of w is # intra vectors - 1, which becomes # of notes - 2
            int occSize = KTables[i][j].w + 2;
            if ((occSize > chains[KTables[i][j].id].size()) && ((pattern.numNotes - occSize) <= 3)){
                vector<pair<int, int>> chain;
                vector<pair<int, int>>& ptr = chain;
                extractChain(KTables[i][j], ptr);
                chains[KTables[i][j].id] = chain;
            }
        }
    }

    ofstream output (file_path);
    int numOccs = chains.size();

    json result;

    for (int i=0; i < chains.size(); i++){
        if (chains[i].size() == 0) continue;
        json occ;
        pair<int, int> maxWindows (getMaxWindowsFromChain(chains[i]));
        occ["matchingPairs"] = chains[i];
        vector<int> targetNotes = filterVectorPairForSecond(chains[i]);
        occ["targetNotes"] = targetNotes;
        occ["size"] = chains[i].size();
        occ["maxPatternWindow"] = maxWindows.first;
        occ["maxTargetWindow"] = maxWindows.second;
        result.push_back(occ);
    }
            
    output << std::setw(4) << result << std::endl;
    output.close();
}
            

int main(int argc, char** argv){

    printf("===== PatternFinder W Algorithm =====\n");

    printf("Loading pattern from indexed path: %s\n", argv[1]);
    Score pattern (argv[1]);
    //pattern.printVectors();

    printf("Loading target from indexed path: %s\n", argv[2]);
    Score target (argv[2]);
    //target.printVectors();

    vector<KEntry> KTables[pattern.numNotes];
    fillKTables(KTables, pattern, target);

    //printKTables(KTables, pattern.numNotes - 1);

    algorithm(KTables, pattern, target);

    writeChainsToJson(KTables, pattern, target, argv[3]);
}
