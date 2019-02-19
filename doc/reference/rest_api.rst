========================= 
REST API reference
=========================

TODO - this documentation requires an overhaul


General Notes
=============

Authentication methods
----------------------
No authentication needed


Data formats
------------
The data format for all input and output data is JSON. Example data will be provided in 
the documentation for each resource. Links within JSON are formatted similar to links in
ATOM, i.e. they will contain the link, a title and a field indicating the relationship.

Most data fields in the responses should be reasonably self-explanatory. In general data fields
and content will be identical to those in the Nimrod database. However, in some cases field names or content were
altered or extra fields added to either satisfy additional requirements of the web service or
as convenience.


Return Codes
------------
Errors are returned using standard HTTP error code syntax. Any additional info is included in the body of the return call, JSON-formatted. Error codes not listed here are in the REST API methods listed below.

+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| Code | Description                                                                                                                             |
+======+=========================================================================================================================================+
| 200  | Ok. Request was successful.                                                                                                             |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 201  | Created. The resource was successfully created. A redirect to the new resource will be set.                                             |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 202  | Accepted. Some request, e.g. starting and stopping jobs, might come in effect after a short delay only.                                 |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 304  | Not modified. This code indicates that the request was successful but the resource was not modified.                                    |
|      | E.g. adding a resource to an experiment that has already been added.                                                                    |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 400  | Bad input parameter. Usually this means that a parameter in the JSON data submitted is missing.                                         |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 401  | Unauthorised. Indicates an authentication problem.                                                                                      |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 403  | Forbidden. You have no access rights to this resource.                                                                                  |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 404  | Not found. Resource does not exists.                                                                                                    | 
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 405  | Method not allowed. This code will be returned when a HTTP method was requested for a resource that not support it.                     |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 409  | Conflict. The request has caused a conflict. E.g. a request to create an experiment that already exists.                                |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 500  | Internal server errror. The error message will indicate what the problem is. If this message comes up, please contact an admin.         |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+
| 501  | Not implemented.                                                                                                                        |
+------+-----------------------------------------------------------------------------------------------------------------------------------------+

Documentation
=============
/nespapi/__doc__
-----------------------
Description
   Return this doc.
URL structure
   https://url/nespapi/__doc__
Method
   GET
Parameters
   None
Returns
   This documentation

User information
================
/nespapi/data
---------------------
Description
   Returns all the data - following wide table format
URL structure
   https://url/nespapi/data
Method
   GET
Parameters
   None
Returns
   All the data.
   