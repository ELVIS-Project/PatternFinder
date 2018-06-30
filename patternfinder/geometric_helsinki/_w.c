#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#include "c_pqueue/pqueue.h"

//#define DEBUG_W

int max(int a, int b){
    return (a > b) ? a : b;
}

int min(int a, int b){
    return (a < b) ? a : b;
}

struct Score {
    struct IntraVector* vectors;
    int num_notes;
    int num_vectors;
};

struct IntraVector {
    float x;
    int y;
    int startIndex;
    int endIndex;
    int startPitch;
    int endPitch;
    int diatonicDiff;
    int chromaticDiff;
};

struct KEntry {
    struct IntraVector patternVec;
    struct IntraVector targetVec;
    float scale;
    int w; // length of occurrence
    int e;
    struct KEntry* y; // backlink for building chains
};

struct Score* load_indexed_score(FILE* data){
    char line[1024];
    struct Score* score = malloc(sizeof(struct Score));

    // Skip the first line which documents the csv headers
    fgets(line, 1024, data);
    // Get the number of notes (assumed to be on the second line)
    fgets(line, 1024, data);
    score->num_notes = atoi(line);
    // Get the number of vectors (assumed to be on the third line)
    fgets(line, 1024, data);
    score->num_vectors = atoi(line);

    // Allocate space for storing vectors
    // (use malloc to create space that is persistent beyond function scope)
    score->vectors = malloc(sizeof(struct IntraVector) * score->num_vectors);

    // Load the rest of the intra vectors
    for (int i=0; i<score->num_vectors; i++){
        fgets(line, 1024, data);
        score->vectors[i].x = atof(strtok(line, ","));
        score->vectors[i].y = atoi(strtok(NULL, ",")); 
        score->vectors[i].startIndex = atoi(strtok(NULL, ",")); 
        score->vectors[i].endIndex = atoi(strtok(NULL, ",")); 
        score->vectors[i].startPitch = atoi(strtok(NULL, ",")); 
        score->vectors[i].endPitch = atoi(strtok(NULL, ",")); 
        //strcpy(score->vectors[i].startPitch, strtok(NULL, ",")); 
        //strcpy(score->vectors[i].endPitch, strtok(NULL, ",")); 
        score->vectors[i].diatonicDiff = atoi(strtok(NULL, ",")); 
        score->vectors[i].chromaticDiff = atoi(strtok(NULL, ",")); 
    }
    return score;
}

void printScore(struct Score* score){
    printf("%d notes\n", score->num_notes);
    printf("%d vectors\n", score->num_vectors);
    for (int i=0; i < score->num_vectors; i++){
        printf("x: %f, y: %d, startIndex: %d, endIndex: %d\n", score->vectors[i].x, score->vectors[i].y, score->vectors[i].startIndex, score->vectors[i].endIndex);
    }
}

void extract_chain(struct KEntry row, int* chain, int* maxTargetWindow, int* transposition, int* diatonicOcc) {
    int curTargetWindow = row.targetVec.endIndex - row.targetVec.startIndex; 
    if (curTargetWindow > *maxTargetWindow) *maxTargetWindow = curTargetWindow;

    if ((row.targetVec.chromaticDiff != row.patternVec.chromaticDiff) && (row.targetVec.diatonicDiff == row.patternVec.diatonicDiff)) {
        *diatonicOcc = 1;
    }

    if (row.y == 0x0) {
        chain[0] = row.targetVec.startIndex;
        chain[1] = row.targetVec.endIndex;

        *transposition = row.patternVec.startPitch - row.targetVec.startPitch;
    }
    else {
        chain[row.w + 1] = row.targetVec.endIndex;
        // Recurse on the backlink
        extract_chain(*(row.y), chain, maxTargetWindow, transposition, diatonicOcc);
    }
}

void write_chains_to_json(struct KEntry** KTables, struct Score* pattern, struct Score* target, FILE* output) {
    int num_occs = 0;

    fprintf(output, "[");
    // Inspect all rows of the final K Table
    for (int i=0; i < target->num_vectors; i++){
        int chain[pattern->num_notes];
        int transposition = 0;
        int maxTargetWindow = 0;
        int diatonicOcc = 0;

        // Full occurrence will be m - 1 vectors, indexed at 0 ==> check for m - 2
        if (KTables[pattern->num_notes - 2][i].w != pattern->num_notes - 2) {
            continue;
        }

        extract_chain(KTables[pattern->num_notes - 2][i], chain, &maxTargetWindow, &transposition, &diatonicOcc);
        num_occs++;

        // Print one occurrence
        if (num_occs == 1) {
            fprintf(output, "{");
        }
        else {
            fprintf(output, ",\n {");
        }

        fprintf(output, "\"targetNotes\": [");
        for (int j=0; j < pattern->num_notes; j++){
            fprintf(output, "%d", chain[j]);
            if (j + 1 != pattern->num_notes){
                fprintf(output, ", ");
            }
        }
        fprintf(output, "], ");

        fprintf(output, "\"transposition\": %d, ", transposition);

        fprintf(output, "\"diatonicOcc\": %s", diatonicOcc ? "true" : "false");


        fprintf(output, "}");
    }
    fprintf(output, "]");

}
            

int compare_K_entries_startIndex(const void* x, const void* y){
    struct KEntry left = *((struct KEntry*) x);
    struct KEntry right = *((struct KEntry*) y);
    if (left.targetVec.startIndex == right.targetVec.startIndex) {
        return left.targetVec.endIndex > right.targetVec.endIndex;
    }
    else {
        return left.targetVec.startIndex > right.targetVec.startIndex;
    }
}
int compare_K_entries_endIndex(const void* x, const void* y){
    struct KEntry left = *((struct KEntry*) x);
    struct KEntry right = *((struct KEntry*) y);
    if (left.targetVec.endIndex == right.targetVec.endIndex) {
        return left.targetVec.startIndex < right.targetVec.startIndex;
    }
    else {
        return left.targetVec.endIndex < right.targetVec.endIndex;
    }
}

struct KEntry** init_K_tables(struct Score* pattern, struct Score* target){

    // Each K table is a list of K entries
    // We have as many K tables as there are notes in the pattern
    struct KEntry** KTables = malloc(pattern->num_vectors * sizeof(struct KEntry*));

    // For now, allocate the max possible size of any K table
    for (int i=0; i < pattern->num_notes - 1; i++) {
        KTables[i] = malloc(target->num_vectors * sizeof(struct KEntry));

        // For W1 only. Filter out for the single pattern vec which goes from i to i + 1
        struct IntraVector curPatternVec;
        for (int m=0; m < pattern->num_vectors; m++){
            curPatternVec = pattern->vectors[m];
            if ((curPatternVec.startIndex == i) && (curPatternVec.endIndex == i + 1)){
                break;
            }
        }

        // Find all db vectors which match the Pi -> Pi+1
        // Could spead up by taking advantage of sorted vectors, or by hashing to y value
        int numMatching = 0;
        for(int j=0; j < target->num_vectors; j++){
            int x = 5;
            if (target->vectors[j].diatonicDiff == curPatternVec.diatonicDiff){
                KTables[i][numMatching].targetVec = target->vectors[j];
                KTables[i][numMatching].patternVec = curPatternVec;
                KTables[i][numMatching].y = NULL;
                numMatching++;
            }
        }
        qsort(KTables[i], numMatching, sizeof(struct KEntry), compare_K_entries_startIndex);
    }
    return KTables;
}

void print_K_table(struct KEntry* KTable, int length){
    for (int i=0; i < length; i ++){
        printf("KEntry %d; y %d; tStart %d; tEnd %d; pStart %d; pEnd %d;\n", i, KTable[i].targetVec.y, KTable[i].targetVec.startIndex, KTable[i].targetVec.endIndex, KTable[i].patternVec.startIndex, KTable[i].patternVec.endIndex);
    }
}

void print_queue(PQueue* queue){
    for (int i=0; i < queue->size; i++){
        struct KEntry* q = pqueue_dequeue(queue);
        printf("targetvec startindex %d\n", q->targetVec.startIndex);
    }
}

void algorithm(struct KEntry** KTables, struct Score* pattern, struct Score* target){
    // TODO find optimal size of K Tables and queues
    //struct KEntry*** Queues = malloc(pattern->num_notes * sizeof(struct KEntry**));
    PQueue** Queues = malloc(pattern->num_notes * sizeof(PQueue*));
    for (int i=0; i < pattern->num_notes; i++){
        Queues[i] = pqueue_new(compare_K_entries_endIndex, target->num_vectors);
    }
    
    // Initialize the first Queue. These are lists of pointers to KEntries
    for (int i=0; i < target->num_vectors; i++){
        // TODO don't add empty KTable rows. find optimal size of KTables and queues..
        if (KTables[0][i].targetVec.startIndex != 0){
            pqueue_enqueue(Queues[1], &KTables[0][i]);
        }
    }


    struct KEntry* q;
    // For all K tables except the first (already copied to queue) (there are m - 1 Ktables)
    for (int i=1; i <= pattern->num_notes - 2; i++){
        if (Queues[i]->size > 0){
            q = pqueue_dequeue(Queues[i]);
        }
        
        // For all rows in the current K Table
        for (int j=0; j < target->num_vectors; j++){
            // Advance the possible antecedent until it matches our first postcedent
            while (q->targetVec.endIndex < KTables[i][j].targetVec.startIndex && Queues[i]->size > 0){
                q = pqueue_dequeue(Queues[i]);
            }

            if (q->targetVec.endIndex == KTables[i][j].targetVec.startIndex){
                // For multiple possible antecedents (multiple chains), take the longest one
                while (((struct KEntry*)Queues[i]->data[0])->targetVec.endIndex == q->targetVec.endIndex && Queues[i]->size > 0){
                    struct KEntry* r = pqueue_dequeue(Queues[i]);
                    if (r->w >= q->w){
                        q = r;
                    }
                }
                KTables[i][j].w = q->w + 1;
                KTables[i][j].y = q;
                pqueue_enqueue(Queues[i+1], &KTables[i][j]);

                if (Queues[i]->size > 0) {
                    q = pqueue_dequeue(Queues[i]);
                }
            }
        }
        KTables[i][target->num_vectors-1].e = 1;
        pqueue_enqueue(Queues[i+1], &KTables[i][target->num_vectors-1]);
    }
}

int main(int argc, char **argv) {

    int streamInput = 0;
    FILE* patternStream;
    FILE* outputStream;
    FILE* targetStream; 

    // FLAGS
    #ifdef DEBUG_W
        printf("Checking flags... first is %s\n", argv[1]);
    #endif
    if (!strcmp(argv[1], "--stream")) {
        #ifdef DEBUG_W
            printf("SELECTED STREAM: Reading pattern from stdin; writing output to stdout\n");
        #endif
        streamInput = 1;
        patternStream = stdin;
        outputStream = stdout;
        targetStream = fopen(argv[2], "r");
    }
    else {
        #ifdef DEBUG_W
            printf("No stream flag \n");
        #endif
        patternStream = fopen(argv[1], "r");
        targetStream = fopen(argv[2], "r");
        outputStream = fopen(argv[3], "w");
    }

    // PARSE INDEXED SCORES
    struct Score *pattern = load_indexed_score(patternStream); 
    #ifdef DEBUG_W
        printf("Pattern Score \n");
        printScore(pattern);
    #endif

    struct Score *target = load_indexed_score(targetStream); 
    #ifdef DEBUG_W
        printScore(target);
    #endif

    // Initialize K tables
    #ifdef DEBUG_W
        printf("init ktables\n");
    #endif

    struct KEntry** KTables = init_K_tables(pattern, target);
    #ifdef DEBUG_W
        for (int i=0; i < pattern->num_notes - 1; i++){
            printf("printing Ktable %d", i);
            print_K_table(KTables[i], 30);
        }
    #endif
     
    
    // Start W line sweeping
    #ifdef DEBUG_W
        printf("Starting algorithm...\n");
    #endif

    algorithm(KTables, pattern, target);

    #ifdef DEBUG_W
        printf("chain analysis\n");
    #endif
    write_chains_to_json(KTables, pattern, target, outputStream);

    // Close file pointer, but not stdin
    if (!streamInput) {
        fclose(outputStream);
    }
    fclose(targetStream);

    return 0;
}
