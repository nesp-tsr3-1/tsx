import subprocess
from tests.util import insert_test_data, import_test_data, compare_output, get_csv_data
import textwrap
from tsx.api.data_import import import_type_2_time_series
from tsx.api.custodian_feedback_shared import update_custodian_feedback_forms
from tsx.api.util import db_session
from sqlalchemy import text

import tempfile
import os

def test_type_2_time_series_import(fresh_database, db_name, output_dir, data_dir):
    import_test_data(db_name, 'unit',
        csv_data="""\
        id,description
        1,Example Unit
        """)

    import_test_data(db_name, 'source',
        csv_data="""\
        id,source_type_id,provider,description,details,authors,notes,contact_name,contact_institution,contact_position,contact_email,contact_phone,time_created,last_modified,monitoring_program_id,monitoring_program_comments,data_processing_type_id,data_agreement_status_id
        1,1,Example Provider,Example Source,Example Source Details,Example Authors,NULL,Example Contact,Example Institution,NA,test@example.com,NULL,2020-01-01 00:00:00,2020-01-01 00:00:00,NULL,NULL,NULL,4
        """)

    import_test_data(db_name, 'taxon_level',
        csv_data="""\
        id,description
        1,sp
        """)

    import_test_data(db_name, 'taxon',
        csv_data="""\
        id,ultrataxon,taxon_level_id,spno,common_name,scientific_name,family_common_name,family_scientific_name,order,population,epbc_status_id,iucn_status_id,state_status_id,bird_action_plan_status_id,national_priority,taxonomic_group,suppress_spatial_representativeness,eligible_for_tsx
        1,0,1,NULL,Example Common Name,Example SciName,Example Family,Example Family SciName,Example Order,Example Population,3,1,NULL,NULL,0,Example Taxonomic Group,0,1
        """)

    import_test_data(db_name, 'search_type',
        csv_data="""\
        id,description
        1,Example Search Type
        """)

    # import_test_data(db_name, 'data_import',
    #     csv_data="""\
    #     source_id,status_id,upload_uuid,filename,error_count,warning_count,data_type,user_id,is_hidden,is_admin
    #     1,7,NULL,NULL,0,0,2,1,0,0
    #     """)

    insert_test_data(db_name, 'user', dict(
        id=1,
        email="test@example.com",
        password_hash="NULL",
        first_name="First",
        last_name="Last",
        phone_number="NULL",
        password_reset_code="NULL",
        time_created='2000-01-01T00:00:00',
        last_modified='2000-01-01T00:00:00'
    ))

    insert_test_data(db_name, 'data_import', dict(
        id=1,
        source_id=1,
        status_id=7,
        upload_uuid="NULL",
        filename="NULL",
        error_count=0,
        warning_count=0,
        data_type=2,
        user_id=1,
        is_hidden=0,
        is_admin=0,
        time_created='2000-01-01T00:00:00',
        last_modified='2000-01-01T00:00:00'
    ))

    # A survey must exist to ensure that data import is considered 'current''
    insert_test_data(db_name, 't2_survey', dict(
        id=1,
        source_id=1,
        start_date_y=2000,
        coords="POINT(0 0)",
        search_type_id=1,
        source_primary_key="1",
        data_import_id=1
    ))

    source_id = 1
    data_import_id = 1

    time_series_csv=textwrap.dedent("""\
    ID,SourceID,SourceDesc,TaxonID,SearchTypeDesc,UnitOfMeasurement,SiteName,SurveysCentroidLatitude,SurveysCentroidLongitude,MonitoringProgram,ManagementCategory,2000,2001,2002,2003,DataType
    1,1,Example Source,1,Example Search Type,Example Unit,Example Site,0,0,,Unknown,1.0,2.0,3.0,4.0,2
    """)

    with tempfile.NamedTemporaryFile(delete_on_close=False) as f:
        f.write(time_series_csv.encode("utf8"))
        f.close()
        import_type_2_time_series(f.name, source_id, data_import_id)


        assert db_session.execute(
            text("SELECT data_import_id, taxon_id FROM data_import_taxon")
        ).fetchall() == [(1, '1')]

