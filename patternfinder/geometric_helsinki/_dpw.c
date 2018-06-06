#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

//#define DEBUG

struct Note {
    double offset;
    int pitch;
};

struct Note* load_notes_from_csv(char *file_path, int *length){
    FILE* data = fopen(file_path, "r");

    // Get the number of notes (assumed to be on the first line)
    char line[1024];
    fgets(line, 1024, data);
    int num_notes = atoi(line);
    *length = num_notes;

    // Allocate space for storing notes
    // (use malloc to create space that is persistent beyond function scope)
    struct Note *notes = malloc(sizeof(struct Note) * num_notes);

    // Load the rest of the notes
    for (int i=0; i<num_notes; i++){
        fgets(line, 1024, data);
        notes[i].offset = atof(strtok(line, ","));
        notes[i].pitch = atoi(strtok(NULL, ",")); 
    }
    fclose(data);
    return notes;
}

void save_matrix_to_json(int ***M, int best, int target_window, int pattern_length, int target_length, char *file_path){
    FILE* output = fopen(file_path, "w");

    fprintf(output, "{\"best\": %d, \n\"matrix\":\n", best);

    fprintf(output, "[");
    for (int i=0; i < target_window + 1; i++){
        fprintf(output, "[");
        
        for (int j=0; j < pattern_length; j++){
            fprintf(output, "[");

            for (int k=0; k < target_length; k++){
                fprintf(output, "%d", M[i][j][k]);
                if (k + 1 != target_length){
                    fprintf(output, ", ");
                }
            }
            fprintf(output, "]");
            if (j + 1 != pattern_length){
                fprintf(output, ",\n");
            }
        }
        fprintf(output, "]");
        if (i + 1 != target_window + 1){
            fprintf(output, ",\n");
        }
    }
    fprintf(output, "]");

    // End JSON hash
    fprintf(output, "\n}");
    fclose(output);
}
            
int max(int a, int b){
    return (a > b) ? a : b;
}
    
void print_notes(struct Note *notes, int length){
    printf("Query has %d notes:\n", length);
    for (int i=0; i<length; i++){
        printf("%f, %d\n", notes[i].offset, notes[i].pitch);
    }
}

int fill_M(int pattern_length, int target_length, int ***M, struct Note *pattern, struct Note *target, int target_window, int cur_p, int cur_t, int last_t_offset){
    /*
    ** cur_p index of current  pattern note
    ** cur_t index of current target note
    ** last_p_offset offset from current pattern note indicating the last pattern note we took
    ** last_p_offset offset from current target note indicating the last target note we took
    ** ex: index of the last p we took is cur_p - last_p_offset
    **/
    int best = 0;
    int a;
    int last_t = cur_t - last_t_offset;
    int last_p = cur_p - 1; //DPW1 exact matches only
    
    // Check the bounds
    if (cur_t >= target_length || cur_p >= pattern_length){
        return 0;
    }

    // Returned a precomputed value
    if (M[last_t_offset][cur_p][cur_t] != -1){
        return M[last_t_offset][cur_p][cur_t];
    }

    // Option 1: Increase chain with cur_t, cur_p as match
    if ((target[cur_t].pitch - target[last_t].pitch)
        == (pattern[cur_p].pitch - pattern[last_p].pitch)){
            a = fill_M(pattern_length, target_length, M, pattern, target, target_window,
                    cur_p + 1,
                    cur_t + 1,
                    1);
            best = max(a + 1, best);
    }

    // Option 2: Try next target note
    if (last_t_offset < target_window){
        a = fill_M(pattern_length, target_length, M, pattern, target, target_window,
                cur_p,
                cur_t + 1,
                last_t_offset + 1);
        best = max(a, best);
    }

    M[last_t_offset][cur_p][cur_t] = best;
    return best;
}

int*** init_M(int target_window, int pattern_length, int target_length){
    #ifdef DEBUG
        printf("Initializing the matrix with...\n"
                "Target window: %d\n"
                "Pattern length: %d\n"
                "Target length: %d\n",
                target_window, pattern_length, target_length); 
        printf("Initializing matrix memory... ");
    #endif
    int ***M = malloc((target_window + 1)* sizeof(int **));
    for (int i=0; i < target_window + 1; i++){
        M[i] = malloc(pattern_length * sizeof(int *));

        for (int j=0; j < pattern_length; j++){
            M[i][j] = malloc(target_length * sizeof(int));
        }
    }

    #ifdef DEBUG
        printf("Filling matrix with -1...\n");
    #endif
    for (int i=0; i < target_window + 1; i++){
        for(int j=0; j < pattern_length; j++){
            for(int k=0; k < target_length; k++){
                M[i][j][k] = -1;
            }
        }
    }
    return M;
}

int main(int argc, char **argv) {
    int target_window = 10;
    char *output_dest = argv[3];

    #ifdef DEBUG
        printf("DPW reading pattern input %s\n", argv[1]);
    #endif
    int pattern_length;
    struct Note *pattern = load_notes_from_csv(argv[1], &pattern_length); 

    #ifdef DEBUG
        print_notes(pattern, pattern_length);
    #endif



    #ifdef DEBUG
        printf("DPW reading mass input %s\n", argv[2]);
    #endif
    int target_length;
    struct Note *target = load_notes_from_csv(argv[2], &target_length); 

    // Initialize matrix to -1
    int ***M = init_M(target_window, pattern_length, target_length);

    // Start dynamic programming algorithm
    #ifdef DEBUG
        printf("Starting algorithm...\n");
    #endif
    int best = 0;
    for (int i=0; i < pattern_length; i++){
        for (int j=0; j < target_length; j++){
            int res = fill_M(pattern_length, target_length, M, pattern, target, target_window, i+1, j+1, 1);
            best = max(res, best);
        }
    }

    save_matrix_to_json(M, best, target_window, pattern_length, target_length, output_dest);

    return 0;
}
