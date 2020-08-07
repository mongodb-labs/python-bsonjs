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

#if PY_MAJOR_VERSION >= 3
#define PyString_FromString PyUnicode_FromString
#endif

PyDoc_STRVAR(bsonjs_documentation,
"A library for converting between BSON and MongoDB Extended JSON.\n"
"\n"
"This module provides the functions `dump(s)` and `load(s)` that wrap\n"
"native libbson functions. https://github.com/mongodb/libbson");

char *
bson_str_to_json(const char *bson, size_t bson_len, size_t *json_len)
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

    json = bson_as_json(b, json_len);

    bson_reader_destroy(reader);

    if (!json) {
        PyErr_SetString(PyExc_ValueError, "invalid BSON document");
        return NULL;
    }

    return json;
}

static PyObject *
_dumps(PyObject *bson)
{
    PyObject *rv;
    char *bson_str, *json;
    Py_ssize_t bson_len;
    size_t json_len;

    bson_str = PyBytes_AS_STRING(bson);
    bson_len = PyBytes_GET_SIZE(bson);

    json = bson_str_to_json(bson_str, (size_t)bson_len, &json_len);
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
"Decode the BSON bytes object `bson` to MongoDB Extended JSON strict mode\n"
"written to `fp` (a `.write()`-supporting file-like object).\n"
"This function wraps `bson_as_json` from libbson.");

static PyObject *
dump(PyObject *self, PyObject *args)
{
    PyObject *bson, *file, *json;

    if (!PyArg_ParseTuple(args, "SO", &bson, &file)) {
        return NULL;
    }

    json = _dumps(bson);
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
"Decode the BSON bytes object `bson` to MongoDB Extended JSON strict mode.\n"
"This function wraps `bson_as_json` from libbson.");

static PyObject *
dumps(PyObject *self, PyObject *args)
{
    PyObject *bson;

    if (!PyArg_ParseTuple(args, "S", &bson)) {
        return NULL;
    }

    return _dumps(bson);
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
    {"dump", dump, METH_VARARGS, dump__doc__},
    {"dumps", dumps, METH_VARARGS, dumps__doc__},
    {"load", load, METH_VARARGS, load__doc__},
    {"loads", loads, METH_VARARGS, loads__doc__},
    {NULL, NULL, 0, NULL}
};

#if PY_MAJOR_VERSION >= 3
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
#else
#define INITERROR return
PyMODINIT_FUNC
initbsonjs(VOID)
#endif
{
#if PY_MAJOR_VERSION >= 3
    PyObject* module = PyModule_Create(&moduledef);
#else
    PyObject* module = Py_InitModule3(
        "bsonjs",
        BsonjsClientMethods,
        bsonjs_documentation);
#endif
    if (module == NULL) {
        INITERROR;
    }

    if (PyModule_AddObject(module,
                           "__version__",
                           PyString_FromString("0.3.0.dev0"))) {
        Py_DECREF(module);
        INITERROR;
    }

#if PY_MAJOR_VERSION >= 3
    return module;
#endif
}
