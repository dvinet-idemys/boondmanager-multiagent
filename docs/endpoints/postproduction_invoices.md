/apps/post-production/projects Type: search Traits: searchable, sortablePaginable

Search projects
GET
Request
Description

Search projects

You can specify the output format by appending to the url .csv
Example : {BASE_URL}/api/apps/post-production/projects.csv?keywords=COMP100
URI Parameters
apiServerrequired, (ui.boondmanager.com), default: ui.boondmanager.com

apiVersionrequired, (1.0), default: 1.0

Query Parameters
allDatasboolean

Retrieve project with PostProduction datas (true by default)
encodingstring

If the output format is csv then encoding filter should be one of :

    UTF-8
    ISO-8859-15
    WINDOWS-1250
    MAC-OS-ROMAN

generateInvoicesboolean

Generate invoices for all projects found
keywordsstring

If keywords = PRJ**ID1** MIS**ID2** COMP**ID3** CCON**ID4** CSOC**ID5** AO**ID6** PROD**ID7** CTR**ID8** then projects :

    of which unique identifier ∈ [ID1] are filtered.
    with deliveries related to them, of which unique identifier ∈ [ID2] are filtered.
    with resources related to them, of which unique identifier ∈ [ID3] are filtered.
    with contacts related to them, of which unique identifier ∈ [ID4] are filtered.
    with companies related to them, of which unique identifier ∈ [ID5] are filtered.
    with opportunities related to them, of which who unique identifier ∈ [ID6] are filtered.
    with products related to them, of which unique identifier ∈ [ID7] are filtered.
    with contracts related to them, of which unique identifier ∈ [ID8] are filtered.

maxResultsnumber between 1-500, default: 30

number of results per page
monthrequired, string matching ^[0-9]{4}-[0-9]{2}$

month
narrowPerimeterboolean

if exists force the kind of join between the types of perimeter used :

    false: Search perfoms OR join
    true: Search perfoms AND join

Types of perimeter depend on parameters : perimeterAgencies, perimeterBus, perimeterPoles & perimeterManagers
orderone of (desc, asc), default: asc

Order's type
pagenumber ≥ 1, default: 1

current page
perimeterAgenciesinteger, repeatable

Results whom responsibles belong to agency's unique identifier are filtered
perimeterBusinessUnitsinteger, repeatable

Results whom responsibles belong to business unit's unique identifier are filtered
perimeterDynamicstring, repeatable

Apply dynamic filtering according to current user context :

    data: Results will belongs to current user
    agencies : Results will be related to current user's agencies
    poles : Results will be related to current user's poles
    businessUnits : Results will be related to current user's business units
    managers : Results will be related to current user's managers (n-1)

perimeterManagersinteger, repeatable

Results whom responsibles belong to manager's unique identifier are filtered
perimeterPolesinteger, repeatable

Results whom responsibles belong to pole's unique identifier are filtered
projectTypesinteger, repeatable

List of project types id to filter (described by /api/rest/application/dictionary/setting.typeOf.project)
sortstring, repeatable

Order by a given column: reference | company.name
