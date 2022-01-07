/*
 * Copyright 2016 MongoDB, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include "bsonjs.h"
#include <bson.h>


PyDoc_STRVAR(bsonjs_documentation,
"A library for converting between BSON and MongoDB Extended JSON.\n"
"\n"
"This module provides the functions `dump(s)` and `load(s)` that wrap\n"
"native libbson functions. https://github.com/mongodb/libbson");

char *
bson_str_to_json(const char *bson, size_t bson_len, size_t *json_len, const
int mode)
{
    char *json;
    const bson_t *b;
    bson_reader_t *reader;

    reader = bson_reader_new_from_data((const uint8_t *)bson, bson_len);

    b = bson_reader_read(reader, NULL);
    if (!b) {
        PyErr_SetString(PyExc_ValueError, "invalid BSON document");
        bson_reader_destroy(reader);
        return NULL;
    }
    if (mode == 1) {
        json = bson_as_relaxed_extended_json(b, json_len);
    } else if (mode == 2) {
        json = bson_as_canonical_extended_json(b, json_len);
    } else if (mode == 0) {
        json = bson_as_json(b, json_len);
    } else {
        PyErr_SetString(PyExc_ValueError, "The value of mode must be one of: "
                                          "bsonjs.RELAXED, bsonjs.LEGACY, "
                                          "or bsonjs.CANONICAL.");
        return NULL;
    }

    bson_reader_destroy(reader);

    if (!json) {
        PyErr_SetString(PyExc_ValueError, "invalid BSON document");
        return NULL;
    }

    return json;
}

static PyObject *
_dumps(PyObject *bson, int mode)
{
    PyObject *rv;
    char *bson_str, *json;
    Py_ssize_t bson_len;
    size_t json_len;

    if (PyBytes_AsStringAndSize(bson, &bson_str, &bson_len) == -1) {
        // error is already set
        return NULL;
    }
    json = bson_str_to_json(bson_str, (size_t)bson_len, &json_len, mode);
    if (!json) {
        // error is already set
        return NULL;
    }

    rv = Py_BuildValue("s#", json, json_len);
    bson_free((void *)json);
    return rv;
}

PyDoc_STRVAR(dump__doc__,
"dump(bson, fp)\n"
"\n"
"Decode the BSON bytes object `bson` to MongoDB Extended JSON 2.0 relaxed\n"
"mode written to `fp` (a `.write()`-supporting file-like object).\n"
"\n"
"Accepts a keyword argument `mode` which can be one of `bsonjs.RELAXED`\n"
"`bsonjs.CANONICAL`, or `bsonjs.LEGACY`. Where `RELAXED` and `CANONICAL` \n"
"correspond to the MongoDB Extended JSON 2.0 modes and `LEGACY` uses libbson's\n"
"legacy JSON format");

static PyObject *
dump(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *bson, *file, *json;
    static char *kwlist[] = {"", "", "mode", NULL};
    int mode = 1;
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "SO|i", kwlist, &bson,
    &file,
    &mode)) {
        return NULL;
    }

    json = _dumps(bson, mode);
    if (!json) {
        return NULL;
    }

    if (PyFile_WriteObject(json, file, Py_PRINT_RAW) == -1) {
        Py_DECREF(json);
        return NULL;
    }

    Py_DECREF(json);
    Py_RETURN_NONE;
}

PyDoc_STRVAR(dumps__doc__,
"dumps(bson) -> str\n"
"\n"
"Decode the BSON bytes object `bson` to MongoDB Extended JSON 2.0 relaxed\n"
"mode. \n"
"Accepts a keyword argument `mode` which can be one of `bsonjs.RELAXED`\n"
"`bsonjs.CANONICAL`, or `bsonjs.LEGACY`. Where `RELAXED` and `CANONICAL` \n"
"correspond to the MongoDB Extended JSON 2.0 modes and `LEGACY` uses libbson's\n"
"legacy JSON format");
static PyObject *
dumps(PyObject *self, PyObject *args, PyObject *kwargs)
{
    PyObject *bson;
    int mode = 1;
    static char *kwlist[] = {"", "mode", NULL};
    if (!PyArg_ParseTupleAndKeywords(args, kwargs, "S|i", kwlist, &bson,
    &mode)) {
        return NULL;
    }
    return _dumps(bson, mode);
}

static PyObject *
_json_to_bson(const char *json, Py_ssize_t json_len) {
    bson_t b = BSON_INITIALIZER;
    bson_error_t error = {0};
    PyObject *bson;

    if (!bson_init_from_json(&b, json, (ssize_t)json_len, &error)) {
        char *msg = "no JSON object could be decoded";
        if (strlen(error.message)) {
            msg = error.message;
        }
        PyErr_SetString(PyExc_ValueError, msg);
        return NULL;
    }

    bson = PyBytes_FromStringAndSize((const char *)bson_get_data(&b), b.len);

    bson_destroy(&b);
    return bson;
}


PyDoc_STRVAR(load__doc__,
"load(fp) -> bytes\n"
"\n"
"Encode `fp` (a `.read()`-supporting file-like object containing a MongoDB\n"
"Extended JSON document) to BSON bytes.\n"
"This function wraps `bson_init_from_json` from libbson.");

static PyObject *
load(PyObject *self, PyObject *args)
{
    char *json_str;
    Py_ssize_t json_len;
    PyObject *file, *json, *bson;

    if (!PyArg_ParseTuple(args, "O", &file)) {
        return NULL;
    }

    json = PyObject_CallMethod(file, "read", NULL);
    if (!json) {
        return NULL;
    }

    // Convert unicode to bytes
    if (PyUnicode_Check(json)) {
        PyObject *json_utf = PyUnicode_AsUTF8String(json);
        Py_DECREF(json);
        if (!json_utf) {
            return NULL;
        }
        json = json_utf;
    }

    if (PyBytes_AsStringAndSize(json, &json_str, &json_len) == -1) {
        return NULL;
    }

    bson = _json_to_bson(json_str, json_len);

    Py_DECREF(json);
    return bson;
}

PyDoc_STRVAR(loads__doc__,
"load(json) -> bytes\n"
"\n"
"Encode `json` (a `str` or `bytes-like object` containing a MongoDB Extended\n"
"JSON document) to BSON bytes.\n"
"This function wraps `bson_init_from_json` from libbson.");

static PyObject *
loads(PyObject *self, PyObject *args)
{
    const char *json_str;
    Py_ssize_t json_len;

    if (!PyArg_ParseTuple(args, "s#", &json_str, &json_len)) {
        return NULL;
    }

    return _json_to_bson(json_str, json_len);
}

static PyMethodDef BsonjsClientMethods[] = {
    {"dump", dump, METH_VARARGS | METH_KEYWORDS, dump__doc__},
    {"dumps", dumps, METH_VARARGS | METH_KEYWORDS, dumps__doc__},
    {"load", load, METH_VARARGS, load__doc__},
    {"loads", loads, METH_VARARGS, loads__doc__},
    {NULL, NULL, 0, NULL}
};


#define INITERROR return NULL

static struct PyModuleDef moduledef = {
    PyModuleDef_HEAD_INIT,
    "bsonjs",
    bsonjs_documentation,
    -1,
    BsonjsClientMethods,
    NULL,
    NULL,
    NULL,
    NULL,
};

PyMODINIT_FUNC
PyInit_bsonjs(VOID)
{
    PyObject* module = PyModule_Create(&moduledef);
    if (module == NULL) {
        INITERROR;
    }

    if (PyModule_AddObject(module,
                           "__version__",
                           PyUnicode_FromString("0.3.0"))) {
        Py_DECREF(module);
        INITERROR;
    }
    PyModule_AddIntConstant(module, "LEGACY", 0);
    PyModule_AddIntConstant(module, "RELAXED", 1);
    PyModule_AddIntConstant(module, "CANONICAL", 2);
    return module;
}
