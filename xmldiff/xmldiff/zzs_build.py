from cffi import FFI

ffibuilder = FFI()

ffibuilder.set_source("xmldiff._zzs", 
                      r""" // passed to the C compiler
// contains implementation of things declared in cdef()
#include <sys/types.h>

typedef struct eElement {
    int operation;
    void * left;
    void * right;
} eElement;

typedef struct eArray {
  int c;
  eElement rgEdits[];
} eArray;

typedef struct cArray {
  int c;
  void * rg[];
} cArray;

extern struct eArray * Distance(void * leftTree, void *  rightTree,
                                struct cArray  *(*callback)(void *),
                                int (*insert)(void *), int (*remove)(void *), 
                                int (*update)(void *, void *));


                      """,
                      sources=["xmldiff/zzs.c"],
                      libraries=[])

ffibuilder.cdef("""

typedef struct eElement {
    int operation;
    void * left;
    void * right;
} eElement;

struct eArray {
  int c;
  eElement rgEdits[];
};

struct cArray {
  int c;
  void * rg[];
};

extern "Python" struct cArray * zzs_get_children(void *);
extern "Python" int zzs_insert_cost(void *);
extern "Python" int zzs_remove_cost(void *);
extern "Python" int zzs_update_cost(void *, void *);


extern struct eArray * Distance(void * leftTree, void *  rightTree,
                                struct cArray  *(*callback)(void *),
                                int (*insert)(void *), int (*remove)(void *), 
                                int (*update)(void *, void *));


"""
            )

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)

