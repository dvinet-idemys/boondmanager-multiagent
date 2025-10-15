/invoices Type: search Traits: searchable, sortablePaginable

Search invoices
GET
POST
Request
Description

Search invoices

You can specify the output format by appending to the url .csv
Example : {BASE_URL}/api/invoices.csv?keywords=FACT1
URI Parameters
apiServerrequired, (ui.boondmanager.com), default: ui.boondmanager.com

apiVersionrequired, (1.0), default: 1.0

Query Parameters
amountnumber

Invoices amountColumn equal to amount
amountColumnstring

    totalExcludingTax : Invoices amount filtered by totalExcludingTax column
    totalIncludingTax : Invoices amount filtered by totalIncludingTax column
    totalPayableIncludingTax : Invoices amount filtered by totalPayableIncludingTax column

amountCurrencyinteger

Currency id to filter (described by /api/rest/application/dictionary/setting.currency)
amountMaxnumber

Invoices amountColumn inferior or equal to amountMax
amountMinnumber

Invoices amountColumn superior or equal to amountMin
amountTypestring

    equal : Invoices amountColumn equal to amount
    between : Invoices amountColumn between amountMin and amountMax

appEntityFieldsstring, repeatable

List of app entity responses filtered by <appId>_<fieldId>:<responseValue> and with html characters encoded
closedboolean

If true returns only invoices/credit notes which are closed, if false returns only invoices/credit notes which are not closed
columnsstring, repeatable

List of columns

    date
    reference
    project
    order
    customer
    state
    expectedPaymentDate
    turnoverInvoicedExcludingTax
    turnoverInvoicedIncludingTax
    totalPayableIncludingTax
    mainManager
    creationDate
    updateDate
    startDate
    endDate
    performedPaymentDate
    billingIntermediary

creditNoteboolean

If true returns only credit notes, if false returns only bills
encodingstring

If the output format is csv then encoding filter should be one of :

    UTF-8
    ISO-8859-15
    WINDOWS-1250
    MAC-OS-ROMAN

endDatestring matching ^[0-9]{4}-[0-9]{2}-[0-9]{2}$|^[0-9]{4}-[0-9]{2}-[0-9]{2}$ [0-9]{2}:[0-9]{2}:[0-9]{2}$

End date
exportToDownloadCenterstring

Export invoices to the download center along with or without the attached documents from the related timesheets:

    documentsAndAttachments
    documentsOnly
    attachmentsOnly
    cii

extractTypestring, default: notDetailed

If the output format is csv then extractType filter should be one of :

    detailed
    notDetailed

flagsinteger, repeatable

Invoices attached to this flag whom flag's unique identifier = integer are filtered
keywordsstring

If keywords = FACT**ID1** BDC**ID2** PRJ**ID3** CCON**ID4** CSOC**ID5** then invoices :

    of which unique identifier ∈ [ID1] are filtered.
    with orders related to them, of which unique identifier ∈ [ID2] are filtered.
    with projects related to them, of which unique identifier ∈ [ID3] are filtered.
    with contacts related to them, of which unique identifier ∈ [ID4] are filtered.
    with companies related to them, of which unique identifier ∈ [ID5] are filtered.

maxResultsnumber between 1-500, default: 30

number of results per page
narrowPerimeterboolean

if exists force the kind of join between the types of perimeter used :

    false: Search perfoms OR join
    true: Search perfoms AND join

Types of perimeter depend on parameters : perimeterAgencies, perimeterBus, perimeterPoles & perimeterManagers
orderone of (desc, asc), default: asc

Order's type
pagenumber ≥ 1, default: 1

current page
paymentMethodsinteger, repeatable

List of payment methods id to filter (described by /api/rest/application/dictionary/setting.paymentMethod)
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
periodstring

    created : Invoices created between startDate and endDate are filtered
    updated : Invoices updated between startDate and endDate are filtered
    expectedPayment : Invoices whose expected payment's is between startDate and endDate are filtered
    performedPayment : Invoices whose performed payment's is between startDate and endDate are filtered
    period : Invoices whose period is between startDate and endDate are filtered
    <appId>_running : App entities whose the period field between startDate and endDate are filtered
    <appId>_started : App entities whose the period field between startDate and endDate are filtered
    <appId>_stopped : App entities whose the period field between startDate and endDate are filtered
    <appId>_fieldId : App entities whose date or datetime field between startDate and endDate are filtered

periodDynamicstring

    today : Invoices filtered according to the grid for today's period
    thisWeek : Invoices filtered according to the mesh for the period of this week
    thisMonth : Invoices filtered according to the mesh for the period of this month
    thisTrimester : Invoices filtered according to the mesh for the period of this trimester
    thisSemester : Invoices filtered according to the mesh for the period of this semester
    thisYear : Invoices filtered according to the mesh for the period of this year
    thisFiscalYear : Invoices filtered according to the mesh for the period of this fiscal year
    yesterday : Invoices filtered according to the mesh for the period of yesterday
    lastWeek : Invoices filtered according to the mesh for the period of last week
    lastMonth : Invoices filtered according to the mesh for the period of last month
    lastTrimester : Invoices filtered according to the mesh for the period of last trimester
    lastSemester : Invoices filtered according to the mesh for the period of last semester
    lastYear : Invoices filtered according to the mesh for the period of last year
    lastFiscalYear : Invoices filtered according to the mesh for the period of last fiscal year
    untilToday : Invoices filtered according to the mesh for the period until today
    tomorrow : Invoices filtered according to the mesh for the period of tomorrow
    nextWeek : Invoices filtered according to the mesh for the period of next week
    nextMonth : Invoices filtered according to the mesh for the period of next month
    nextTrimester : Invoices filtered according to the mesh for the period of next trimester
    nextSemester : Invoices filtered according to the mesh for the period of next semester
    nextYear : Invoices filtered according to the mesh for the period of next year
    nextFiscalYear : Invoices filtered according to the mesh for the period of next fiscal year
    lastCustomPeriod : Invoices filtered according to the mesh from the last custom period until now
    nextCustomPeriod : Invoices filtered according to the mesh for the next custom period from now

periodDynamicParametersstring

Filter parameters of dynamic period. Used when periodDynamic is "lastCustomPeriod" or "nextCustomPeriod"
You need two values separated by "," (duration,unit) eg (3,months)

    1,n : Duration of the custom period (max 100)
    days,weeks,months,trimesters,semesters,years : Unit of the custom period

projectTypesinteger, repeatable

List of project types id to filter (described by /api/rest/application/dictionary/setting.typeOf.project)
sortstring, repeatable

Order by a given column: turnoverInvoicedIncludingTax | date | reference | turnoverInvoicedExcludingTax | expectedPaymentDate | state | order.number | order.project.reference | order.project.company.name | order.mainManager.lastName | closed | startDate | endDate | intermediaryCompany.name
startDatestring matching ^[0-9]{4}-[0-9]{2}-[0-9]{2}$|^[0-9]{4}-[0-9]{2}-[0-9]{2}$ [0-9]{2}:[0-9]{2}:[0-9]{2}$

Start date
statesinteger, repeatable

List of invoice states id to filter (described by /api/rest/application/dictionary/setting.state.invoice)

---

/invoices/{id} Type: profile

Manage invoice's profile
GET
Request
Description

Get invoice's basic data
URI Parameters
apiServerrequired, (ui.boondmanager.com), default: ui.boondmanager.com

apiVersionrequired, (1.0), default: 1.0

idrequired, string

Invoice's unique identifier

---

/invoices/{id}/information Type: profile

Get invoice's information data (much more detailed)
GET
Request
Description

Get invoice's information data
URI Parameters
apiServerrequired, (ui.boondmanager.com), default: ui.boondmanager.com

apiVersionrequired, (1.0), default: 1.0

idrequired, string

Invoice's unique identifier
