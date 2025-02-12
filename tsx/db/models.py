from typing import Any, List, Optional

from sqlalchemy import CHAR, Column, Computed, Date, Double, ForeignKeyConstraint, Index, Integer, SmallInteger, String, TIMESTAMP, Table, Text, Time, text
from sqlalchemy.dialects.mysql import MEDIUMTEXT, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import NullType
import datetime
import decimal

class Base(DeclarativeBase):
    pass


class DataImportStatus(Base):
    __tablename__ = 'data_import_status'
    __table_args__ = (
        Index('code_UNIQUE', 'code', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(255))


class DataProcessingType(Base):
    __tablename__ = 'data_processing_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class IntensiveManagement(Base):
    __tablename__ = 'intensive_management'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))
    grouping: Mapped[Optional[str]] = mapped_column(String(255))


class Management(Base):
    __tablename__ = 'management'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))
    type: Mapped[Optional[str]] = mapped_column(String(255))


class MonitoringProgram(Base):
    __tablename__ = 'monitoring_program'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))
    summary: Mapped[Optional[str]] = mapped_column(MEDIUMTEXT)
    lead: Mapped[Optional[str]] = mapped_column(String(255))

    user: Mapped[List['User']] = relationship('User', secondary='user_program_manager')


class ProjectionName(Base):
    __tablename__ = 'projection_name'

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    epsg_srid: Mapped[int] = mapped_column(Integer)


class Range(Base):
    __tablename__ = 'range'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class Region(Base):
    __tablename__ = 'region'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    geometry: Mapped[str] = mapped_column(NullType)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    state: Mapped[Optional[str]] = mapped_column(String(255))
    positional_accuracy_in_m: Mapped[Optional[int]] = mapped_column(Integer)
    centroid: Mapped[Optional[str]] = mapped_column(NullType, Computed('(st_centroid(`geometry`))', persisted=True))

    survey: Mapped[List['T1Survey']] = relationship('T1Survey', secondary='t1_survey_region')


t_region_subdiv = Table(
    'region_subdiv', Base.metadata,
    Column('id', Integer, nullable=False),
    Column('name', String(255)),
    Column('geometry', NullType, nullable=False)
)


class ResponseVariableType(Base):
    __tablename__ = 'response_variable_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))


class Role(Base):
    __tablename__ = 'role'
    __table_args__ = (
        Index('name_UNIQUE', 'description', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))

    user: Mapped[List['User']] = relationship('User', secondary='user_role')


class SearchType(Base):
    __tablename__ = 'search_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class SourceType(Base):
    __tablename__ = 'source_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class State(Base):
    __tablename__ = 'state'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    geometry: Mapped[Optional[str]] = mapped_column(NullType)


class TaxonLevel(Base):
    __tablename__ = 'taxon_level'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class TaxonSourceAlphaHull(Base):
    __tablename__ = 'taxon_source_alpha_hull'

    taxon_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_type: Mapped[str] = mapped_column(String(255), primary_key=True)
    core_range_area_in_m2: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True))
    geometry: Mapped[Optional[str]] = mapped_column(NullType)
    alpha_hull_area_in_m2: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))


class TaxonStatus(Base):
    __tablename__ = 'taxon_status'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[Optional[str]] = mapped_column(String(255))


class TimeSeriesInclusion(Base):
    __tablename__ = 'time_series_inclusion'

    time_series_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    sample_years: Mapped[int] = mapped_column(TINYINT(1))
    master_list_include: Mapped[int] = mapped_column(TINYINT(1))
    search_type: Mapped[int] = mapped_column(TINYINT(1))
    taxon_status: Mapped[int] = mapped_column(TINYINT(1))
    region: Mapped[int] = mapped_column(TINYINT(1))
    data_agreement: Mapped[int] = mapped_column(TINYINT(1))
    standardisation_of_method_effort: Mapped[int] = mapped_column(TINYINT(1))
    consistency_of_monitoring: Mapped[int] = mapped_column(TINYINT(1))
    non_zero: Mapped[int] = mapped_column(TINYINT(1))
    include_in_analysis: Mapped[Optional[int]] = mapped_column(TINYINT(1), Computed('(((0 <> `sample_years`) and (0 <> `master_list_include`) and (0 <> `search_type`) and (0 <> `taxon_status`) and (0 <> `region`) and (0 <> `data_agreement`) and (0 <> `standardisation_of_method_effort`) and (0 <> `consistency_of_monitoring`) and (0 <> `non_zero`)))', persisted=False))


class Unit(Base):
    __tablename__ = 'unit'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class UnitType(Base):
    __tablename__ = 'unit_type'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    description: Mapped[str] = mapped_column(String(255))


class User(Base):
    __tablename__ = 'user'
    __table_args__ = (
        Index('email_UNIQUE', 'email', unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), comment='\t')
    password_hash: Mapped[Optional[str]] = mapped_column(Text)
    first_name: Mapped[Optional[str]] = mapped_column(Text)
    last_name: Mapped[Optional[str]] = mapped_column(Text)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32))
    password_reset_code: Mapped[Optional[str]] = mapped_column(String(32))
    time_created: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    last_modified: Mapped[Optional[datetime.datetime]] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))


class Source(Base):
    __tablename__ = 'source'
    __table_args__ = (
        ForeignKeyConstraint(['data_processing_type_id'], ['data_processing_type.id'], name='fk_source_data_processing_type1'),
        ForeignKeyConstraint(['monitoring_program_id'], ['monitoring_program.id'], ondelete='SET NULL', onupdate='CASCADE', name='fk_source_monitoring_program1'),
        ForeignKeyConstraint(['source_type_id'], ['source_type.id'], name='fk_Source_SourceType'),
        Index('fk_Source_SourceType_idx', 'source_type_id'),
        Index('fk_source_data_processing_type1_idx', 'data_processing_type_id'),
        Index('fk_source_monitoring_program1_idx', 'monitoring_program_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    time_created: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    last_modified: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    source_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    provider: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    details: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    authors: Mapped[Optional[str]] = mapped_column(Text)
    contact_name: Mapped[Optional[str]] = mapped_column(Text)
    contact_institution: Mapped[Optional[str]] = mapped_column(Text)
    contact_position: Mapped[Optional[str]] = mapped_column(Text)
    contact_email: Mapped[Optional[str]] = mapped_column(Text)
    contact_phone: Mapped[Optional[str]] = mapped_column(Text)
    monitoring_program_id: Mapped[Optional[int]] = mapped_column(Integer)
    monitoring_program_comments: Mapped[Optional[str]] = mapped_column(Text)
    data_processing_type_id: Mapped[Optional[int]] = mapped_column(Integer)

    data_processing_type: Mapped['DataProcessingType'] = relationship('DataProcessingType')
    monitoring_program: Mapped['MonitoringProgram'] = relationship('MonitoringProgram')
    source_type: Mapped['SourceType'] = relationship('SourceType')
    user: Mapped[List['User']] = relationship('User', secondary='user_source')


class Taxon(Base):
    __tablename__ = 'taxon'
    __table_args__ = (
        ForeignKeyConstraint(['bird_action_plan_status_id'], ['taxon_status.id'], name='fk_taxon_taxon_status1'),
        ForeignKeyConstraint(['epbc_status_id'], ['taxon_status.id'], name='fk_taxon_taxon_status2'),
        ForeignKeyConstraint(['iucn_status_id'], ['taxon_status.id'], name='fk_taxon_taxon_status3'),
        ForeignKeyConstraint(['state_status_id'], ['taxon_status.id'], name='fk_taxon_taxon_status4'),
        ForeignKeyConstraint(['taxon_level_id'], ['taxon_level.id'], name='fk_Taxon_TaxonLevel1'),
        Index('fk_Taxon_TaxonLevel1_idx', 'taxon_level_id'),
        Index('fk_taxon_taxon_status1_idx', 'bird_action_plan_status_id'),
        Index('fk_taxon_taxon_status2_idx', 'epbc_status_id'),
        Index('fk_taxon_taxon_status3_idx', 'iucn_status_id'),
        Index('fk_taxon_taxon_status4_idx', 'state_status_id'),
        Index('spno', 'spno')
    )

    id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    ultrataxon: Mapped[int] = mapped_column(TINYINT(1))
    scientific_name: Mapped[str] = mapped_column(String(255))
    national_priority: Mapped[int] = mapped_column(TINYINT(1), server_default=text("'0'"))
    taxonomic_group: Mapped[str] = mapped_column(String(255))
    suppress_spatial_representativeness: Mapped[int] = mapped_column(TINYINT(1), server_default=text("'0'"))
    taxon_level_id: Mapped[Optional[int]] = mapped_column(Integer)
    spno: Mapped[Optional[int]] = mapped_column(SmallInteger)
    common_name: Mapped[Optional[str]] = mapped_column(String(255))
    family_common_name: Mapped[Optional[str]] = mapped_column(String(255))
    family_scientific_name: Mapped[Optional[str]] = mapped_column(String(255))
    order: Mapped[Optional[str]] = mapped_column(String(255))
    population: Mapped[Optional[str]] = mapped_column(String(255))
    epbc_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    iucn_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    state_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    bird_action_plan_status_id: Mapped[Optional[int]] = mapped_column(Integer)
    max_status_id: Mapped[Optional[int]] = mapped_column(Integer, Computed('(nullif(greatest(coalesce(`epbc_status_id`,0),coalesce(`iucn_status_id`,0),coalesce(`bird_action_plan_status_id`,0)),0))', persisted=False))

    bird_action_plan_status: Mapped['TaxonStatus'] = relationship('TaxonStatus', foreign_keys=[bird_action_plan_status_id])
    epbc_status: Mapped['TaxonStatus'] = relationship('TaxonStatus', foreign_keys=[epbc_status_id])
    iucn_status: Mapped['TaxonStatus'] = relationship('TaxonStatus', foreign_keys=[iucn_status_id])
    state_status: Mapped['TaxonStatus'] = relationship('TaxonStatus', foreign_keys=[state_status_id])
    taxon_level: Mapped['TaxonLevel'] = relationship('TaxonLevel')


t_user_program_manager = Table(
    'user_program_manager', Base.metadata,
    Column('user_id', Integer, primary_key=True, nullable=False),
    Column('monitoring_program_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['monitoring_program_id'], ['monitoring_program.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_user_program_manager_monitoring_program1'),
    ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', onupdate='CASCADE', name='fk_user_program_manager_user1'),
    Index('fk_user_program_manager_monitoring_program1_idx', 'monitoring_program_id'),
    Index('fk_user_program_manager_user1_idx', 'user_id')
)


t_user_role = Table(
    'user_role', Base.metadata,
    Column('user_id', Integer, primary_key=True, nullable=False),
    Column('role_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['role_id'], ['role.id'], name='fk_user_role_role1'),
    ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_user_role_user1'),
    Index('fk_user_role_role1_idx', 'role_id')
)


t_aggregated_by_month = Table(
    'aggregated_by_month', Base.metadata,
    Column('start_date_y', SmallInteger, nullable=False),
    Column('start_date_m', SmallInteger),
    Column('site_id', Integer),
    Column('search_type_id', Integer),
    Column('taxon_id', CHAR(8), nullable=False),
    Column('response_variable_type_id', Integer, nullable=False),
    Column('value', Double(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', Integer, nullable=False),
    Column('region_id', Integer),
    Column('unit_id', Integer, nullable=False),
    Column('positional_accuracy_in_m', Double(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32), Computed("(concat(`source_id`,_utf8mb4'_',`unit_id`,_utf8mb4'_',coalesce(`search_type_id`,_utf8mb4'0'),_utf8mb4'_',`site_id`,_utf8mb4'_',`taxon_id`))", persisted=False)),
    ForeignKeyConstraint(['region_id'], ['region.id'], name='fk_aggregated_by_month_region1'),
    ForeignKeyConstraint(['response_variable_type_id'], ['response_variable_type.id'], name='fk_aggregated_by_month_response_variable_type1'),
    ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_aggregated_by_month_search_type1'),
    ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_aggregated_by_month_source1'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_aggregated_by_month_taxon1'),
    ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_aggregated_by_month_unit1'),
    Index('fk_aggregated_by_month_region1_idx', 'region_id'),
    Index('fk_aggregated_by_month_response_variable_type1_idx', 'response_variable_type_id'),
    Index('fk_aggregated_by_month_search_type1_idx', 'search_type_id'),
    Index('fk_aggregated_by_month_source1_idx', 'source_id'),
    Index('fk_aggregated_by_month_taxon1_idx', 'taxon_id'),
    Index('fk_aggregated_by_month_unit1_idx', 'unit_id')
)


t_aggregated_by_year = Table(
    'aggregated_by_year', Base.metadata,
    Column('start_date_y', SmallInteger, nullable=False),
    Column('site_id', Integer),
    Column('search_type_id', Integer),
    Column('taxon_id', CHAR(8), nullable=False),
    Column('response_variable_type_id', Integer, nullable=False),
    Column('value', Double(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', Integer, nullable=False),
    Column('region_id', Integer),
    Column('unit_id', Integer, nullable=False),
    Column('positional_accuracy_in_m', Double(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32), Computed("(concat(`source_id`,_utf8mb4'_',`unit_id`,_utf8mb4'_',coalesce(`search_type_id`,_utf8mb4'0'),_utf8mb4'_',`site_id`,_utf8mb4'_',`taxon_id`))", persisted=False)),
    Column('include_in_analysis', TINYINT(1), nullable=False, server_default=text("'0'")),
    ForeignKeyConstraint(['region_id'], ['region.id'], name='fk_aggregated_by_year_region1'),
    ForeignKeyConstraint(['response_variable_type_id'], ['response_variable_type.id'], name='fk_aggregated_by_year_response_variable_type1'),
    ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_aggregated_by_year_search_type1'),
    ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_aggregated_by_year_source1'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_aggregated_by_year_taxon1'),
    ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_aggregated_by_year_unit1'),
    Index('fk_aggregated_by_year_region1_idx', 'region_id'),
    Index('fk_aggregated_by_year_response_variable_type1_idx', 'response_variable_type_id'),
    Index('fk_aggregated_by_year_search_type1_idx', 'search_type_id'),
    Index('fk_aggregated_by_year_source1_idx', 'source_id'),
    Index('fk_aggregated_by_year_taxon1_idx', 'taxon_id'),
    Index('fk_aggregated_by_year_unit1_idx', 'unit_id')
)


class DataImport(Base):
    __tablename__ = 'data_import'
    __table_args__ = (
        ForeignKeyConstraint(['source_id'], ['source.id'], name='fk_data_import_source1'),
        ForeignKeyConstraint(['status_id'], ['data_import_status.id'], name='fk_data_import_data_import_status1'),
        ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_data_import_user1'),
        Index('fk_data_import_data_import_status1_idx', 'status_id'),
        Index('fk_data_import_source1_idx', 'source_id'),
        Index('fk_data_import_user1_idx', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    data_type: Mapped[int] = mapped_column(Integer)
    is_hidden: Mapped[int] = mapped_column(TINYINT(1), server_default=text("'0'"))
    time_created: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    last_modified: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'))
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    status_id: Mapped[Optional[int]] = mapped_column(Integer)
    upload_uuid: Mapped[Optional[str]] = mapped_column(String(36))
    filename: Mapped[Optional[str]] = mapped_column(Text)
    error_count: Mapped[Optional[int]] = mapped_column(Integer)
    warning_count: Mapped[Optional[int]] = mapped_column(Integer)
    user_id: Mapped[Optional[int]] = mapped_column(Integer)

    source: Mapped['Source'] = relationship('Source')
    status: Mapped['DataImportStatus'] = relationship('DataImportStatus')
    user: Mapped['User'] = relationship('User')


class DataProcessingNotes(Base):
    __tablename__ = 'data_processing_notes'
    __table_args__ = (
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_data_processing_notes_source1'),
        ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_data_processing_notes_user1'),
        Index('fk_data_processing_notes_source1_idx', 'source_id'),
        Index('fk_data_processing_notes_user1_idx', 'user_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[int] = mapped_column(Integer)
    time_created: Mapped[datetime.datetime] = mapped_column(TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    notes: Mapped[str] = mapped_column(Text)

    source: Mapped['Source'] = relationship('Source')
    user: Mapped['User'] = relationship('User')


class DataSource(Base):
    __tablename__ = 'data_source'
    __table_args__ = (
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_data_source_source1'),
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_data_source_taxon1'),
        Index('fk_data_source_taxon1_idx', 'taxon_id')
    )

    source_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    taxon_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    exclude_from_analysis: Mapped[int] = mapped_column(TINYINT(1))
    suppress_aggregated_data: Mapped[int] = mapped_column(TINYINT(1))
    data_agreement_id: Mapped[Optional[int]] = mapped_column(Integer)
    objective_of_monitoring_id: Mapped[Optional[int]] = mapped_column(Integer)
    absences_recorded: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    standardisation_of_method_effort_id: Mapped[Optional[int]] = mapped_column(Integer)
    consistency_of_monitoring_id: Mapped[Optional[int]] = mapped_column(Integer)
    start_year: Mapped[Optional[int]] = mapped_column(Integer)
    end_year: Mapped[Optional[int]] = mapped_column(Integer)
    citation: Mapped[Optional[str]] = mapped_column(Text)

    source: Mapped['Source'] = relationship('Source')
    taxon: Mapped['Taxon'] = relationship('Taxon')


t_incidental_sighting = Table(
    'incidental_sighting', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('coords', NullType),
    Column('date', Date),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_incidental_sighting_taxon1'),
    Index('fk_incidental_sighting_taxon1_idx', 'taxon_id')
)


t_processing_method = Table(
    'processing_method', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('unit_id', Integer),
    Column('source_id', Integer, nullable=False),
    Column('search_type_id', Integer),
    Column('data_type', Integer, nullable=False),
    Column('response_variable_type_id', Integer, nullable=False),
    Column('positional_accuracy_threshold_in_m', Double(asdecimal=True)),
    ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_processing_method_search_type1'),
    ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_processing_method_source1'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_processing_method_taxon1'),
    ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_processing_method_unit1'),
    Index('fk_processing_method_search_type1_idx', 'search_type_id'),
    Index('fk_processing_method_source1_idx', 'source_id'),
    Index('fk_processing_method_unit1_idx', 'unit_id'),
    Index('uniq', 'taxon_id', 'unit_id', 'source_id', 'search_type_id', 'data_type', unique=True)
)


class TaxonGroup(Base):
    __tablename__ = 'taxon_group'
    __table_args__ = (
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_taxon_group_taxon1'),
        Index('fk_taxon_group_taxon1_idx', 'taxon_id'),
        Index('taxon_group_subgroup', 'taxon_id', 'group_name', 'subgroup_name', unique=True)
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    taxon_id: Mapped[str] = mapped_column(CHAR(8))
    group_name: Mapped[str] = mapped_column(String(255))
    subgroup_name: Mapped[Optional[str]] = mapped_column(String(255))

    taxon: Mapped['Taxon'] = relationship('Taxon')


class TaxonHybrid(Base):
    __tablename__ = 'taxon_hybrid'
    __table_args__ = (
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_TaxonHybrid_Taxon1'),
        Index('fk_TaxonHybrid_Taxon1_idx', 'taxon_id')
    )

    id: Mapped[str] = mapped_column(CHAR(12), primary_key=True, comment='e.g. u123a.b.c')
    taxon_id: Mapped[Optional[str]] = mapped_column(CHAR(8))

    taxon: Mapped['Taxon'] = relationship('Taxon')


t_taxon_presence_alpha_hull = Table(
    'taxon_presence_alpha_hull', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('range_id', Integer, nullable=False),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False),
    ForeignKeyConstraint(['range_id'], ['range.id'], name='fk_taxon_presence_alpha_hull_range1'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_taxon_presence_alpha_hull_taxon1'),
    Index('fk_taxon_presence_alpha_hull_range1_idx', 'range_id'),
    Index('fk_taxon_presence_alpha_hull_taxon1', 'taxon_id')
)


t_taxon_presence_alpha_hull_subdiv = Table(
    'taxon_presence_alpha_hull_subdiv', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('range_id', Integer, nullable=False),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False),
    ForeignKeyConstraint(['range_id'], ['range.id'], name='fk_taxon_presence_alpha_hull_range10'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_taxon_presence_alpha_hull_taxon10'),
    Index('fk_taxon_presence_alpha_hull_range1_idx', 'range_id'),
    Index('fk_taxon_presence_alpha_hull_taxon10', 'taxon_id')
)


t_taxon_range = Table(
    'taxon_range', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('range_id', Integer, nullable=False),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False),
    ForeignKeyConstraint(['breeding_range_id'], ['range.id'], name='fk_taxon_range_range2'),
    ForeignKeyConstraint(['range_id'], ['range.id'], name='fk_taxon_range_range1'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_taxon_range_taxon1'),
    Index('fk_taxon_range_range1_idx', 'range_id'),
    Index('fk_taxon_range_range2_idx', 'breeding_range_id'),
    Index('fk_taxon_range_taxon1_idx', 'taxon_id')
)


t_taxon_range_subdiv = Table(
    'taxon_range_subdiv', Base.metadata,
    Column('taxon_id', CHAR(8), nullable=False),
    Column('range_id', Integer, nullable=False),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False),
    ForeignKeyConstraint(['breeding_range_id'], ['range.id'], name='fk_taxon_range_range20'),
    ForeignKeyConstraint(['range_id'], ['range.id'], name='fk_taxon_range_range10'),
    ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_taxon_range_taxon10'),
    Index('fk_taxon_range_range1_idx', 'range_id'),
    Index('fk_taxon_range_range2_idx', 'breeding_range_id'),
    Index('fk_taxon_range_taxon1_idx', 'taxon_id')
)


t_user_source = Table(
    'user_source', Base.metadata,
    Column('user_id', Integer, primary_key=True, nullable=False),
    Column('source_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['source_id'], ['source.id'], name='fk_user_source_source1'),
    ForeignKeyConstraint(['user_id'], ['user.id'], name='fk_user_source_user1'),
    Index('fk_user_source_source1_idx', 'source_id')
)


class T1Site(Base):
    __tablename__ = 't1_site'
    __table_args__ = (
        ForeignKeyConstraint(['data_import_id'], ['data_import.id'], ondelete='CASCADE', name='fk_t1_site_data_import1'),
        ForeignKeyConstraint(['intensive_management_id'], ['intensive_management.id'], name='fk_t1_site_intensive_management1'),
        ForeignKeyConstraint(['management_id'], ['management.id'], name='fk_t1_site_management1'),
        ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_T1Site_SearchType1'),
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_T1Site_Source1'),
        Index('fk_T1Site_SearchType1_idx', 'search_type_id'),
        Index('fk_T1Site_Source1_idx', 'source_id'),
        Index('fk_t1_site_data_import1_idx', 'data_import_id'),
        Index('fk_t1_site_intensive_management1_idx', 'intensive_management_id'),
        Index('fk_t1_site_management1_idx', 'management_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    search_type_id: Mapped[int] = mapped_column(Integer)
    data_import_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    intensive_management_id: Mapped[Optional[int]] = mapped_column(Integer)
    management_id: Mapped[Optional[int]] = mapped_column(Integer)
    management_comments: Mapped[Optional[str]] = mapped_column(Text)

    data_import: Mapped['DataImport'] = relationship('DataImport')
    intensive_management: Mapped['IntensiveManagement'] = relationship('IntensiveManagement')
    management: Mapped['Management'] = relationship('Management')
    search_type: Mapped['SearchType'] = relationship('SearchType')
    source: Mapped['Source'] = relationship('Source')


class T2Site(Base):
    __tablename__ = 't2_site'
    __table_args__ = (
        ForeignKeyConstraint(['data_import_id'], ['data_import.id'], ondelete='CASCADE', name='fk_t2_site_data_import1'),
        ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_t2_site_search_type1'),
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_t2_site_source1'),
        Index('fk_t2_site_data_import1_idx', 'data_import_id'),
        Index('fk_t2_site_search_type1_idx', 'search_type_id'),
        Index('fk_t2_site_source1_idx', 'source_id'),
        Index('source_name', 'source_id', 'name')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    search_type_id: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[Optional[int]] = mapped_column(Integer)
    data_import_id: Mapped[Optional[int]] = mapped_column(Integer)
    name: Mapped[Optional[str]] = mapped_column(String(255))

    data_import: Mapped['DataImport'] = relationship('DataImport')
    search_type: Mapped['SearchType'] = relationship('SearchType')
    source: Mapped['Source'] = relationship('Source')
    survey: Mapped[List['T2Survey']] = relationship('T2Survey', secondary='t2_survey_site')


class T1Survey(Base):
    __tablename__ = 't1_survey'
    __table_args__ = (
        ForeignKeyConstraint(['data_import_id'], ['data_import.id'], ondelete='CASCADE', name='fk_t1_survey_data_import1'),
        ForeignKeyConstraint(['site_id'], ['t1_site.id'], ondelete='CASCADE', name='fk_T1Survey_T1Site1'),
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_T1Survey_Source1'),
        Index('fk_T1Survey_Source1_idx', 'source_id'),
        Index('fk_T1Survey_T1Site1_idx', 'site_id'),
        Index('fk_t1_survey_data_import1_idx', 'data_import_id'),
        Index('source_primary_key_UNIQUE', 'source_primary_key', unique=True)
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    site_id: Mapped[int] = mapped_column(Integer)
    source_id: Mapped[int] = mapped_column(Integer)
    source_primary_key: Mapped[str] = mapped_column(String(255))
    start_date_y: Mapped[int] = mapped_column(SmallInteger)
    coords: Mapped[str] = mapped_column(NullType)
    data_import_id: Mapped[Optional[int]] = mapped_column(Integer)
    start_date_d: Mapped[Optional[int]] = mapped_column(SmallInteger)
    start_date_m: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_d: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_m: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_y: Mapped[Optional[int]] = mapped_column(SmallInteger)
    start_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    finish_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    duration_in_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    area_in_m2: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    length_in_km: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    number_of_traps_per_day: Mapped[Optional[int]] = mapped_column(Integer)
    location: Mapped[Optional[str]] = mapped_column(Text)
    positional_accuracy_in_m: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    comments: Mapped[Optional[str]] = mapped_column(Text)

    data_import: Mapped['DataImport'] = relationship('DataImport')
    site: Mapped['T1Site'] = relationship('T1Site')
    source: Mapped['Source'] = relationship('Source')


class T2Survey(Base):
    __tablename__ = 't2_survey'
    __table_args__ = (
        ForeignKeyConstraint(['data_import_id'], ['data_import.id'], ondelete='CASCADE', name='fk_t2_survey_data_import1'),
        ForeignKeyConstraint(['search_type_id'], ['search_type.id'], name='fk_T2Survey_SearchType1'),
        ForeignKeyConstraint(['site_id'], ['t2_site.id'], ondelete='CASCADE', name='fk_t2_survey_t2_site1'),
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_T1Survey_Source10'),
        Index('fk_T1Survey_Source1_idx', 'source_id'),
        Index('fk_T2Survey_SearchType1_idx', 'search_type_id'),
        Index('fk_t2_survey_data_import1_idx', 'data_import_id'),
        Index('fk_t2_survey_t2_site1_idx', 'site_id'),
        Index('source_primary_key_UNIQUE', 'source_primary_key', unique=True)
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_id: Mapped[int] = mapped_column(Integer)
    start_date_y: Mapped[int] = mapped_column(SmallInteger)
    coords: Mapped[str] = mapped_column(NullType)
    search_type_id: Mapped[int] = mapped_column(Integer)
    source_primary_key: Mapped[str] = mapped_column(String(255))
    site_id: Mapped[Optional[int]] = mapped_column(Integer)
    data_import_id: Mapped[Optional[int]] = mapped_column(Integer)
    start_date_d: Mapped[Optional[int]] = mapped_column(SmallInteger)
    start_date_m: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_d: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_m: Mapped[Optional[int]] = mapped_column(SmallInteger)
    finish_date_y: Mapped[Optional[int]] = mapped_column(SmallInteger)
    start_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    finish_time: Mapped[Optional[datetime.time]] = mapped_column(Time)
    duration_in_minutes: Mapped[Optional[int]] = mapped_column(Integer)
    area_in_m2: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    length_in_km: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    location: Mapped[Optional[str]] = mapped_column(Text)
    positional_accuracy_in_m: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    comments: Mapped[Optional[str]] = mapped_column(Text)
    secondary_source_id: Mapped[Optional[str]] = mapped_column(String(255))

    data_import: Mapped['DataImport'] = relationship('DataImport')
    search_type: Mapped['SearchType'] = relationship('SearchType')
    site: Mapped['T2Site'] = relationship('T2Site')
    source: Mapped['Source'] = relationship('Source')


class T1Sighting(Base):
    __tablename__ = 't1_sighting'
    __table_args__ = (
        ForeignKeyConstraint(['survey_id'], ['t1_survey.id'], ondelete='CASCADE', name='fk_T1Sighting_T1Survey1'),
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_T1Sighting_Taxon1'),
        ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_T1Sighting_Unit1'),
        ForeignKeyConstraint(['unit_type_id'], ['unit_type.id'], name='fk_t1_sighting_unit_type1'),
        Index('fk_T1Sighting_T1Survey1_idx', 'survey_id'),
        Index('fk_T1Sighting_Taxon1_idx', 'taxon_id'),
        Index('fk_T1Sighting_Unit1_idx', 'unit_id'),
        Index('fk_t1_sighting_unit_type1_idx', 'unit_type_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(Integer)
    taxon_id: Mapped[str] = mapped_column(CHAR(8))
    count: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True))
    unit_id: Mapped[int] = mapped_column(Integer)
    unit_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    breeding: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    comments: Mapped[Optional[str]] = mapped_column(Text)

    survey: Mapped['T1Survey'] = relationship('T1Survey')
    taxon: Mapped['Taxon'] = relationship('Taxon')
    unit: Mapped['Unit'] = relationship('Unit')
    unit_type: Mapped['UnitType'] = relationship('UnitType')


t_t1_survey_region = Table(
    't1_survey_region', Base.metadata,
    Column('survey_id', Integer, primary_key=True),
    Column('region_id', Integer, nullable=False),
    ForeignKeyConstraint(['region_id'], ['region.id'], ondelete='CASCADE', name='fk_t1_survey_region_region1'),
    ForeignKeyConstraint(['survey_id'], ['t1_survey.id'], ondelete='CASCADE', name='fk_t1_survey_region_t1_survey1'),
    Index('fk_t1_survey_region_region1_idx', 'region_id'),
    Index('fk_t1_survey_region_t1_survey1_idx', 'survey_id')
)


class T2ProcessedSurvey(Base):
    __tablename__ = 't2_processed_survey'
    __table_args__ = (
        ForeignKeyConstraint(['raw_survey_id'], ['t2_survey.id'], ondelete='CASCADE', name='fk_t2_processed_survey_t2_survey1'),
        ForeignKeyConstraint(['site_id'], ['t2_site.id'], ondelete='CASCADE', name='fk_t2_processed_survey_t2_site1'),
        ForeignKeyConstraint(['source_id'], ['source.id'], ondelete='CASCADE', name='fk_t2_processed_survey_source1'),
        Index('fk_t2_processed_survey_source1_idx', 'source_id'),
        Index('fk_t2_processed_survey_t2_site1_idx', 'site_id'),
        Index('fk_t2_processed_survey_t2_survey1_idx', 'raw_survey_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    raw_survey_id: Mapped[int] = mapped_column(Integer)
    search_type_id: Mapped[int] = mapped_column(Integer)
    start_date_y: Mapped[int] = mapped_column(SmallInteger)
    source_id: Mapped[int] = mapped_column(Integer)
    site_id: Mapped[Optional[int]] = mapped_column(Integer)
    start_date_m: Mapped[Optional[int]] = mapped_column(SmallInteger)

    raw_survey: Mapped['T2Survey'] = relationship('T2Survey')
    site: Mapped['T2Site'] = relationship('T2Site')
    source: Mapped['Source'] = relationship('Source')


class T2Sighting(Base):
    __tablename__ = 't2_sighting'
    __table_args__ = (
        ForeignKeyConstraint(['survey_id'], ['t2_survey.id'], ondelete='CASCADE', name='fk_T2Sighting_T2Survey1'),
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_T2Sighting_Taxon1'),
        ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_T2Sighting_Unit1'),
        ForeignKeyConstraint(['unit_type_id'], ['unit_type.id'], name='fk_t2_sighting_unit_type1'),
        Index('fk_T2Sighting_T2Survey1_idx', 'survey_id'),
        Index('fk_T2Sighting_Taxon1_idx', 'taxon_id'),
        Index('fk_T2Sighting_Unit1_idx', 'unit_id'),
        Index('fk_t2_sighting_unit_type1_idx', 'unit_type_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(Integer)
    taxon_id: Mapped[str] = mapped_column(CHAR(8))
    count: Mapped[Optional[decimal.Decimal]] = mapped_column(Double(asdecimal=True))
    unit_id: Mapped[Optional[int]] = mapped_column(Integer)
    breeding: Mapped[Optional[int]] = mapped_column(TINYINT(1))
    unit_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    comments: Mapped[Optional[str]] = mapped_column(Text)

    survey: Mapped['T2Survey'] = relationship('T2Survey')
    taxon: Mapped['Taxon'] = relationship('Taxon')
    unit: Mapped['Unit'] = relationship('Unit')
    unit_type: Mapped['UnitType'] = relationship('UnitType')


t_t2_survey_site = Table(
    't2_survey_site', Base.metadata,
    Column('survey_id', Integer, primary_key=True, nullable=False),
    Column('site_id', Integer, primary_key=True, nullable=False),
    ForeignKeyConstraint(['site_id'], ['t2_site.id'], ondelete='CASCADE', name='fk_T2SurveySite_T2Site1'),
    ForeignKeyConstraint(['survey_id'], ['t2_survey.id'], ondelete='CASCADE', name='fk_T2SurveySite_T2Survey1'),
    Index('fk_T2SurveySite_T2Site1_idx', 'site_id')
)


class T2ProcessedSighting(Base):
    __tablename__ = 't2_processed_sighting'
    __table_args__ = (
        ForeignKeyConstraint(['survey_id'], ['t2_processed_survey.id'], ondelete='CASCADE', name='fk_t2_processed_sighting_t2_processed_survey1'),
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_t2_processed_sighting_taxon1'),
        ForeignKeyConstraint(['unit_id'], ['unit.id'], name='fk_t2_processed_sighting_unit1'),
        Index('fk_t2_processed_sighting_taxon1_idx', 'taxon_id'),
        Index('fk_t2_processed_sighting_unit1_idx', 'unit_id'),
        Index('survey_id_taxon_id', 'survey_id', 'taxon_id')
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    survey_id: Mapped[int] = mapped_column(Integer)
    taxon_id: Mapped[str] = mapped_column(CHAR(8))
    count: Mapped[decimal.Decimal] = mapped_column(Double(asdecimal=True))
    unit_id: Mapped[int] = mapped_column(Integer)
    pseudo_absence: Mapped[int] = mapped_column(TINYINT(1))

    survey: Mapped['T2ProcessedSurvey'] = relationship('T2ProcessedSurvey')
    taxon: Mapped['Taxon'] = relationship('Taxon')
    unit: Mapped['Unit'] = relationship('Unit')


class T2UltrataxonSighting(Base):
    __tablename__ = 't2_ultrataxon_sighting'
    __table_args__ = (
        ForeignKeyConstraint(['range_id'], ['range.id'], name='fk_T2SightingRangeType_RangeType1'),
        ForeignKeyConstraint(['sighting_id'], ['t2_sighting.id'], ondelete='CASCADE', name='fk_T2ProcessedSighting_T2Sighting1'),
        ForeignKeyConstraint(['taxon_id'], ['taxon.id'], name='fk_T2ProcessedSighting_Taxon1'),
        Index('fk_T2ProcessedSighting_Taxon1_idx', 'taxon_id'),
        Index('fk_T2SightingRangeType_RangeType1_idx', 'range_id')
    )

    sighting_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    taxon_id: Mapped[str] = mapped_column(CHAR(8), primary_key=True)
    range_id: Mapped[int] = mapped_column(Integer)
    generated_subspecies: Mapped[int] = mapped_column(TINYINT(1))

    range: Mapped['Range'] = relationship('Range')
    sighting: Mapped['T2Sighting'] = relationship('T2Sighting')
    taxon: Mapped['Taxon'] = relationship('Taxon')
