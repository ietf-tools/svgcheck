#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <assert.h>

#define _CrtCheckMemory()

int compare(const void * a, const void * b)
{
    return (*(int*)a - *(int *)b);
}

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


struct xxx {
    int i;
};

typedef struct intArray {
    int cItems;
    int cAlloc;
    int * rgValues;
} intArray;

typedef struct ptrArray {
    int cItems;
    int cAlloc;
    void ** rgValues;
} ptrArray;

struct snode {
    void * treeNode;
    intArray anc;
    struct snode *   pNext;
};

struct pnode {
    void * treeNode;
    int nodeId;
    intArray anc;
	int hasChildren;
    struct pnode * pNext;
};

struct aTree {
    int i;
    int       size;

    intArray  lmds;
    ptrArray  nodes;
    intArray  ids;
    intArray  keyroots;
};

void cloneIntArray(intArray * dest, intArray * src)
{
    dest->cItems = src->cItems;
    dest->cAlloc = 20;
    if (dest->cItems+20 > dest->cAlloc) {
	dest->cAlloc = dest->cItems + 5;
    }
    
    dest->rgValues = (int *) calloc(sizeof(int), dest->cAlloc);
    if (dest->rgValues == NULL) {
	//  error
    }
    memcpy(dest->rgValues, src->rgValues, src->cItems*sizeof(int));
}

void appendLeft(intArray * dest, int newValue)
{
    if (dest->cItems == dest->cAlloc) {
	int * newArray = (int *) calloc(sizeof(int), dest->cItems+10);
	memcpy(newArray, dest->rgValues, dest->cItems*sizeof(int));
	free(dest->rgValues);
	dest->rgValues = newArray;
	dest->cAlloc += 10;
    }
    memmove(&dest->rgValues[1], &dest->rgValues[0], dest->cItems*sizeof(int));
    dest->rgValues[0] = newValue;
    dest->cItems += 1;
}

void append(intArray * dest, int newValue)
{
    if (dest->cItems == dest->cAlloc) {
	int * newArray = (int *) calloc(sizeof(int), dest->cItems+10);
	memcpy(newArray, dest->rgValues, dest->cItems*sizeof(int));
	free(dest->rgValues);
	dest->rgValues = newArray;
	dest->cAlloc += 10;
    }
    dest->rgValues[dest->cItems] = newValue;
    dest->cItems += 1;
}

void appendNode(ptrArray * dest, void * newValue)
{
    if (dest->cItems == dest->cAlloc) {
	void ** newArray = (void **) calloc(sizeof(void *), dest->cItems+10);
	memcpy(newArray, dest->rgValues, dest->cItems*sizeof(void *));
	free(dest->rgValues);
	dest->rgValues = newArray;
	dest->cAlloc += 10;
    }
    dest->rgValues[dest->cItems] = newValue;
    dest->cItems += 1;
}


struct aTree * AnnotateTree(void * root, struct cArray *(*get_children)(void *))
{
	int i;
	int lmd;
	int j = 0;
	int c;
	int jj;
	struct snode * stack = NULL;
	struct pnode * pstack = NULL;
	struct aTree * self = NULL;
	int * lmds = NULL;
	int * keyroots = NULL;
	struct snode * snew = (struct snode *) calloc(sizeof(struct snode), 1);
	if (snew == NULL) {
	  return NULL;
	}
	snew->treeNode = root;
	snew->pNext = stack;
	stack = snew;

	while (stack != NULL) {
		struct snode * sthis = stack;
		int nid = j;

		struct cArray * children = get_children(sthis->treeNode);
		struct pnode * pnew;
		stack = stack->pNext;

		for (c = 0; c < children->c; c++) {
			snew = (struct snode *) calloc(sizeof(struct snode), 1);
			snew->treeNode = children->rg[c];
			cloneIntArray(&snew->anc, &sthis->anc);
			appendLeft(&snew->anc, nid);
			snew->pNext = stack;
			stack = snew;
		}
		pnew = (struct pnode *) calloc(sizeof(struct pnode), 1);
		pnew->treeNode = sthis->treeNode;
		pnew->nodeId = nid;
		pnew->anc = sthis->anc;
		pnew->hasChildren = children->c != 0;
		pnew->pNext = pstack;
		pstack = pnew;
		j += 1;

		free(sthis);
		// free(children);
	}

	self = (struct aTree *) calloc(sizeof(struct aTree), 1);
	self->size = j;

	lmds = (int *)malloc(sizeof(int) * j);
	memset(lmds, -1, sizeof(int)*j);
	keyroots = (int *)malloc(sizeof(int) * j);
	memset(keyroots, -1, sizeof(int)*j);

	i = 0;
	while (pstack != NULL) {
		struct pnode * pthis = pstack;
		pstack = pstack->pNext;

		appendNode(&self->nodes, pthis->treeNode);
		append(&self->ids, pthis->nodeId);

		if (!pthis->hasChildren) {
			int ii;
			lmd = i;
			for (ii = 0; ii < pthis->anc.cItems; ii++) {
				int a = pthis->anc.rgValues[ii];
				if (lmds[a] == -1) {
					lmds[a] = i;
				}
				else {
					break;
				}
			}
		}
		else {
			lmd = lmds[pthis->nodeId];
		}
		append(&self->lmds, lmd);
		keyroots[lmd] = i;
		i += 1;

		free(pthis->anc.rgValues);
		free(pthis);
	}

	qsort(keyroots, j, sizeof(int), compare);

	for (jj = 0; jj < j; jj++) {
		if (keyroots[jj] != -1) {
			if (self->keyroots.rgValues == NULL) {
				self->keyroots.cAlloc = j - jj;
				self->keyroots.rgValues = (int *) calloc(sizeof(int), self->keyroots.cAlloc);
			}
			self->keyroots.rgValues[self->keyroots.cItems] = keyroots[jj];
			self->keyroots.cItems += 1;
		}
	}

	free(lmds);
	free(keyroots);

	return self;
}

#define index(a, b) ((a)*n + (b))
#define tindex(x, y) ((x)*(b->size) + y)

#define OP_INSERT 1
#define OP_REMOVE 2
#define OP_UPDATE 3
#define OP_MATCH 4
#define OP_COMBINE 5
#define OP_COMBINE_MATCH 6
#define OP_COMBINE_UPDATE 7
#define OP_LIST 8

typedef struct editList {
    int  operation;
    int  cost;
    void * left;
    void * right;
	void * three;
} EditList;

void Combine(EditList * pdest, EditList * pleft, EditList * pright)
{
	pdest->operation = OP_COMBINE;
	pdest->cost = 0;
	if (pleft != NULL) {
		pdest->cost += pleft->cost;
		pdest->left = pleft;
	}
	if (pright != NULL) {
		pdest->cost += pright->cost;
		pdest->right = pright;
	}
}

void UpdateAndCombine(EditList * pdest, EditList * pleft, void * left, void * right, int cost)
{
	pdest->operation = cost ? OP_COMBINE_UPDATE : OP_COMBINE_MATCH;
	pdest->cost = cost;
	pdest->right = left;
	pdest->three = right;
	if (pleft != NULL) {
		pdest->cost += pleft->cost;
		pdest->left = pleft;
	}
}

int countList(struct eArray * psrc)
{
	int c = 0;
	int i;
	for (i = 0; i < psrc->c; i++) {
		switch (psrc->rgEdits[i].operation) {
		case OP_LIST:
			c += countList((struct eArray *) (psrc->rgEdits[i].left));
			break;

		default:
			c += 1;
		}
	}
	return c;
}

int cloneCount(EditList * p, int fAll)
{
	switch (p->operation) {
	case OP_LIST:
		if (fAll) {
			return countList((struct eArray *) ((struct cArray *) p->left));
		}
		return 1;

	case OP_INSERT:
	case OP_REMOVE:
		return 1;

	case OP_COMBINE:
		return cloneCount((EditList *) p->left, fAll) + cloneCount((EditList *) p->right, fAll);

	case OP_COMBINE_MATCH:
	case OP_COMBINE_UPDATE:
		return cloneCount((EditList *) p->left, fAll) + 1;

	default:
		return 0;
	}
}

void copyList(eArray * pdst, eArray * psrc)
{
	int i;
	for (i = 0; i < psrc->c; i++) {
		switch (psrc->rgEdits[i].operation) {
		case OP_LIST:
			copyList(pdst, (struct eArray *) psrc->rgEdits[i].left);
			break;

		default:
			pdst->rgEdits[pdst->c].operation = psrc->rgEdits[i].operation;
			pdst->rgEdits[pdst->c].left = psrc->rgEdits[i].left;
			pdst->rgEdits[pdst->c].right = psrc->rgEdits[i].right;
			pdst->c += 1;
			break;
		}
	}
}

void fillArray(eArray * pa, EditList * p, int fAll)
{
	switch (p->operation) {
	case OP_LIST:
		if (fAll) {
			struct eArray * pca = (struct eArray *) p->left;
			copyList(pa, pca);
			return;
		}
		pa->rgEdits[pa->c].operation = OP_LIST;
		pa->rgEdits[pa->c].left = p->left;
		pa->c += 1;
		return;

	case OP_INSERT:
	case OP_REMOVE:
		pa->rgEdits[pa->c].operation = p->operation;
		pa->rgEdits[pa->c].left = p->left;
		pa->rgEdits[pa->c].right = p->right;
		pa->c += 1;
		return;

	case OP_COMBINE:
		fillArray(pa, (EditList *) p->left, fAll);
		fillArray(pa, (EditList *) p->right, fAll);
		return;

	case OP_COMBINE_MATCH:
	case OP_COMBINE_UPDATE:
		fillArray(pa, (EditList *) p->left, fAll);
		pa->rgEdits[pa->c].operation = p->operation == OP_COMBINE_MATCH ? OP_MATCH : OP_UPDATE;
		pa->rgEdits[pa->c].left = p->right;
		pa->rgEdits[pa->c].right = p->three;
		pa->c += 1;
		return;

	default:
		return;
	}
}

EditList * cloneEdits(EditList * p2clone, int fAll)
{
	int c = cloneCount(p2clone, fAll);
	EditList * pret = NULL;
	
	eArray * pEA = (eArray *)calloc(sizeof(eArray) + sizeof(eElement) * c, 1);
	pEA->c = 0;
	fillArray(pEA, p2clone, fAll);

	pret = (EditList *)calloc(sizeof(EditList), 1);
	pret->operation = OP_LIST;
	pret->left = pEA;
	pret->cost = p2clone->cost;

	return pret;
}

struct eArray * Distance(void * leftTree, void * rightTree, struct cArray *(*get_children)(void *),
	int(*insert_cost)(void *), int(*remove_cost)(void *),
	int(*update_cost)(void *, void *))
{
	struct aTree * a = AnnotateTree(leftTree, get_children);
	struct aTree * b = AnnotateTree(rightTree, get_children);

	EditList ** treedists = (EditList **)calloc(sizeof(EditList *), (a->size)*(b->size));
	EditList * a_remove = (EditList *)calloc(sizeof(EditList), (a->size));
	EditList * b_insert = (EditList *)calloc(sizeof(EditList), (b->size));

	EditList * fd = (EditList *)malloc(sizeof(EditList) * (a->size+1) * (b->size+1));
	EditList * pret = NULL;
	eArray * pret2;
	
	int i;
	int i_1;

	for (i = 0; i < a->size; i++) {
		a_remove[i].operation = OP_REMOVE;
		a_remove[i].cost = remove_cost(a->nodes.rgValues[i]);
		a_remove[i].left = a->nodes.rgValues[i];
	}

	for (i = 0; i < b->size; i++) {
		b_insert[i].operation = OP_INSERT;
		b_insert[i].cost = insert_cost(b->nodes.rgValues[i]);
		b_insert[i].right = b->nodes.rgValues[i];
	}

	for (i_1 = 0; i_1 < a->keyroots.cItems; i_1++) {
		int i = a->keyroots.rgValues[i_1];
		// _CrtCheckMemory();
		int j_1;
		for (j_1 = 0; j_1 < b->keyroots.cItems; j_1++) {
			int j = b->keyroots.rgValues[j_1];
			int m = i - a->lmds.rgValues[i] + 2;
			int n = j - b->lmds.rgValues[j] + 2;
			int ioff = a->lmds.rgValues[i] - 1;
			int joff = b->lmds.rgValues[j] - 1;
			int x;
			int y;
			
			_CrtCheckMemory();

			memset(fd, 0, sizeof(EditList)*m*n);
			assert(treedists != NULL);
			_CrtCheckMemory();


			_CrtCheckMemory();
			
			for (x = 1; x < m; x++) {
				Combine(&fd[index(x, 0)], &fd[index(x - 1, 0)], &a_remove[x + ioff]);
			}
			_CrtCheckMemory();

			for (y = 1; y < n; y++) {
				Combine(&fd[index(0, y)], &fd[index(0, y - 1)], &b_insert[y + joff]);
			}

			for (x = 1; x < m; x++) {
				for (y = 1; y < n; y++) {
				  // _CrtCheckMemory();
					int x_ioff = x + ioff;
					int y_joff = y + joff;

					if (a->lmds.rgValues[i] == a->lmds.rgValues[x_ioff] && b->lmds.rgValues[j] == b->lmds.rgValues[y_joff]) {
						//                    +-
						//                    | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
						//  δ(F1 , F2 ) = min-+ δ(l(i1)..i , l(j1)..j-1) + γ(λ → w)
						//                    | δ(l(i1)..i-1, l(j1)..j-1) + γ(v → w)
						//                    +-

						int cost2Update = update_cost(a->nodes.rgValues[x_ioff], b->nodes.rgValues[y_joff]);

						int op1Cost = fd[index(x - 1, y)].cost + a_remove[x_ioff].cost;
						int op2Cost = fd[index(x, y - 1)].cost + b_insert[y_joff].cost;
						int op3Cost = fd[index(x - 1, y - 1)].cost + cost2Update;

						if (op1Cost < op2Cost) {
							if (op1Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x - 1, y)], &a_remove[x_ioff]);
							}
							else if (op2Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x, y - 1)], &b_insert[y_joff]);
							}
							else {
								UpdateAndCombine(&fd[index(x, y)], &fd[index(x - 1, y - 1)], a->nodes.rgValues[x_ioff], b->nodes.rgValues[y_joff], cost2Update);
							}
						}
						else {
							if (op2Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x, y - 1)], &b_insert[y_joff]);
							}
							else {
								UpdateAndCombine(&fd[index(x, y)], &fd[index(x - 1, y - 1)], a->nodes.rgValues[x_ioff], b->nodes.rgValues[y_joff], cost2Update);
							}
						}
						_CrtCheckMemory();

						treedists[tindex(x_ioff, y_joff)] = cloneEdits(&fd[index(x, y)], 0);
						_CrtCheckMemory();
					}
					else {
						// #                   +-
						// #                   | δ(l(i1)..i-1, l(j1)..j) + γ(v → λ)
						// # δ(F1, F2) = min - +δ(l(i1)..i, l(j1)..j - 1) + γ(λ → w)
						// #                   | δ(l(i1)..l(i)-1, l(j1)..l(j)-1)
						// #                   |                     + treedist(i1,j1)
						// #                   +-

						int p = a->lmds.rgValues[x_ioff] - 1 - ioff;
						int q = b->lmds.rgValues[y_joff] - 1 - joff;

						int op1Cost = fd[index(x - 1, y)].cost + a_remove[x_ioff].cost;
						int op2Cost = fd[index(x, y - 1)].cost + b_insert[y_joff].cost;
					  int op3Cost = fd[index(p, q)].cost + ((treedists[tindex(x_ioff, y_joff)] != NULL) ? treedists[tindex(x_ioff, y_joff)]->cost : 0);

						if (op1Cost < op2Cost) {
							if (op1Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x - 1, y)], &a_remove[x_ioff]);
							}
							else if (op2Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x, y - 1)], &b_insert[y_joff]);
							}
							else {
								Combine(&fd[index(x, y)], &fd[index(p, q)], treedists[tindex(x_ioff, y_joff)]);
							}
						}
						else {
							if (op2Cost < op3Cost) {
								Combine(&fd[index(x, y)], &fd[index(x, y - 1)], &b_insert[y_joff]);
							}
							else {
								Combine(&fd[index(x, y)], &fd[index(p, q)], treedists[tindex(x_ioff, y_joff)]);
							}
						}
						_CrtCheckMemory();
					}
				}
			}
		}
	}
	_CrtCheckMemory();

	free(fd);

	pret = cloneEdits(treedists[tindex(a->size - 1, b->size - 1)], 1);

	for (i=0; i<a->size*b->size; i++) {
	  if (treedists[i]->operation == OP_LIST) {
	    free(treedists[i]->left);
	    free(treedists[i]);
	  }
	}
	free(treedists);
	free(a_remove);
	free(b_insert);

	pret2 = pret->left;
	free(pret);
	// M00TODO finish freeing everything
	return pret2;
}
