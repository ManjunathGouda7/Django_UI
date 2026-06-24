from django.urls import path

from .views_uichecks import (
    # General
    UpdateProductCategoryJSONView,
    GetProductsView,
    GetCategoryView,

    # Testcase setup (Tags/Suits)
    GetTestTagsView,
    PostNewTestTagView,
    GetTestSuitsView,
    PostNewTestsuitView,

    # Testcase setup (Headers)
    PutTestHeaderView,
    GetTestHeaderView,
    DeleteTestHeaderView,

    # Testcase setup (Steps)
    PutTCStepView,
    GetTCStepsView,
    PutUpdateTCStepView,
    GetStepIDView,
    DeleteTCStepsView,

    # Testcase setup (Actions)
    GetActionsListView,
    PutActionsView,
    GetActionsView,
    DeleteActionsView,

    # POM
    AddWebPageView,
    GetWebpagesView,
    GetFramesView,
    GetElementsView,
    GetAllElementsView,
    GetElementTypeView,
    PostElementView,
    GetElementView,
    UpdateElementView,
    DeleteElementView,

    # Runner
    GetTestDataView,
    GetJobListView,
    DeleteJobView,

    # Project
    CreateProjectView,
    GetProjectView,
    DeleteProjectView,
    UpdateProjectView,

    # Project execution
    AddTestDataRunView,
    DeleteTestDataRunView,
    GetTestDataRunView,

    # Reports
    ReportTestHeadersView,
    ReportTestStepsView,
    ReportStepActionsView,
    DetailedUIReportView,
    UploadResultJSONView,

    # Existing
    PostTestHeaderView,
)

urlpatterns = [
    # General
    path(
        'UpdateProductCategoryJSON/<str:Product>/<str:Category>/',
        UpdateProductCategoryJSONView.as_view(),
        name='uichecks_update_product_category_json',
    ),
    path('GetProducts/', GetProductsView.as_view(), name='uichecks_get_products'),
    path('GetCategory/<str:product_name>/', GetCategoryView.as_view(), name='uichecks_get_category'),

    # Tags
    path('GetTestTags/', GetTestTagsView.as_view(), name='uichecks_get_test_tags'),
    path('PostTestTag/<str:tag_name>/', PostNewTestTagView.as_view(), name='uichecks_post_test_tag'),

    # Suits
    path('GetTestSuits/', GetTestSuitsView.as_view(), name='uichecks_get_test_suits'),
    path(
        'PostTestsuit/<str:testsuit>/',
        PostNewTestsuitView.as_view(),
        name='uichecks_post_test_suit',
    ),

    # Headers
    path('PostTestHeader/', PostTestHeaderView.as_view(), name='uichecks_post_test_header'),
    path(
        'PutTestHeader/<str:TestID>/<str:Product>/<str:Category>/',
        PutTestHeaderView.as_view(),
        name='uichecks_put_test_header',
    ),
    path('GetTestcases/', GetTestHeaderView.as_view(), name='uichecks_get_testcases'),
    path('DeleteTestHeader/', DeleteTestHeaderView.as_view(), name='uichecks_delete_test_header'),

    # Steps
    path('PutTCStep/<str:TestID>/<str:Product>/<str:Category>/', PutTCStepView.as_view(), name='uichecks_put_tc_step'),
    path('GetTCSteps/', GetTCStepsView.as_view(), name='uichecks_get_tc_steps'),
    path(
        'PutUpdateTCStep/<str:Product>/<str:Category>/<str:TestID>/<str:StepID>/',
        PutUpdateTCStepView.as_view(),
        name='uichecks_put_update_tc_step',
    ),
    path('GetStepID/<str:TestID>/', GetStepIDView.as_view(), name='uichecks_get_step_id'),
    path('DeleteTCSteps/', DeleteTCStepsView.as_view(), name='uichecks_delete_tc_steps'),

    # Actions
    path('GetActionsList/', GetActionsListView.as_view(), name='uichecks_get_actions_list'),
    path(
        'PutActions/<str:Product>/<str:Category>/<str:TestID>/<str:StepID>/',
        PutActionsView.as_view(),
        name='uichecks_put_actions',
    ),
    path('GetActions/', GetActionsView.as_view(), name='uichecks_get_actions'),
    path('DeleteActions/', DeleteActionsView.as_view(), name='uichecks_delete_actions'),

    # POM (Webpages/Frames/Elements)
    path('AddWebPage/', AddWebPageView.as_view(), name='uichecks_add_webpage'),
    path('GetWebpages/<str:Product>/<str:Category>/', GetWebpagesView.as_view(), name='uichecks_get_webpages'),
    path('GetFrames/<str:Product>/<str:Category>/<str:Webpage>/', GetFramesView.as_view(), name='uichecks_get_frames'),
    path('GetElements/<str:Product>/<str:Category>/<str:Webpage>/<str:Frame>/', GetElementsView.as_view(), name='uichecks_get_elements'),
    path('GetAllElements/', GetAllElementsView.as_view(), name='uichecks_get_all_elements'),
    path('GetElementType/', GetElementTypeView.as_view(), name='uichecks_get_element_type'),
    path('PostElement/', PostElementView.as_view(), name='uichecks_post_element'),
    path('GetElement/', GetElementView.as_view(), name='uichecks_get_element'),
    path('UpdateElement/', UpdateElementView.as_view(), name='uichecks_update_element'),
    path('DeleteElement/', DeleteElementView.as_view(), name='uichecks_delete_element'),

    # Runner
    path('GetTestData/', GetTestDataView.as_view(), name='uichecks_get_test_data'),
    path('GetJobList/', GetJobListView.as_view(), name='uichecks_get_job_list'),
    path('DeleteJob/', DeleteJobView.as_view(), name='uichecks_delete_job'),

    # Project
    path('CreateProject/', CreateProjectView.as_view(), name='uichecks_create_project'),
    path('GetProject/', GetProjectView.as_view(), name='uichecks_get_project'),
    path('DeleteProject/', DeleteProjectView.as_view(), name='uichecks_delete_project'),
    path('UpdateProject/', UpdateProjectView.as_view(), name='uichecks_update_project'),

    # Project execution
    path('AddTestDataRun/', AddTestDataRunView.as_view(), name='uichecks_add_test_data_run'),
    path('DeleteTestDataRun/', DeleteTestDataRunView.as_view(), name='uichecks_delete_test_data_run'),
    path('GetTestDataRun/', GetTestDataRunView.as_view(), name='uichecks_get_test_data_run'),

    # Reports
    path('ReportTestHeaders/', ReportTestHeadersView.as_view(), name='uichecks_report_test_headers'),
    path('ReportTestSteps/<str:TestID>/', ReportTestStepsView.as_view(), name='uichecks_report_test_steps'),
    path(
        'ReportStepActions/<str:TestID>/<str:StepID>/',
        ReportStepActionsView.as_view(),
        name='uichecks_report_step_actions',
    ),
    path('DetailedUIReport/', DetailedUIReportView.as_view(), name='uichecks_detailed_ui_report'),
    path('UploadResultJSON/', UploadResultJSONView.as_view(), name='uichecks_upload_result_json'),
]




