# coding: utf-8
from sqlalchemy import Column, Date, DateTime, Float, ForeignKey, Index, Integer, SmallInteger, String, Table, Text, Time, text
from sqlalchemy.sql.sqltypes import NullType
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()
metadata = Base.metadata


t_aggregated_by_month = Table(
    'aggregated_by_month', metadata,
    Column('start_date_y', SmallInteger, nullable=False),
    Column('start_date_m', SmallInteger),
    Column('site_id', Integer),
    Column('grid_cell_id', ForeignKey('grid_cell.id'), index=True),
    Column('search_type_id', ForeignKey('search_type.id'), index=True),
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('experimental_design_type_id', ForeignKey('experimental_design_type.id'), nullable=False, index=True),
    Column('response_variable_type_id', ForeignKey('response_variable_type.id'), nullable=False, index=True),
    Column('value', Float(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('region_id', ForeignKey('region.id'), index=True),
    Column('unit_id', ForeignKey('unit.id'), nullable=False, index=True),
    Column('positional_accuracy_in_m', Float(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32))
)


t_aggregated_by_year = Table(
    'aggregated_by_year', metadata,
    Column('start_date_y', SmallInteger, nullable=False),
    Column('site_id', Integer),
    Column('grid_cell_id', ForeignKey('grid_cell.id'), index=True),
    Column('search_type_id', ForeignKey('search_type.id'), index=True),
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('experimental_design_type_id', ForeignKey('experimental_design_type.id'), nullable=False, index=True),
    Column('response_variable_type_id', ForeignKey('response_variable_type.id'), nullable=False, index=True),
    Column('value', Float(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('region_id', ForeignKey('region.id'), index=True),
    Column('unit_id', ForeignKey('unit.id'), nullable=False, index=True),
    Column('positional_accuracy_in_m', Float(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32)),
    Column('include_in_analysis', Integer, nullable=False, server_default=text("'0'"))
)


class DataImport(Base):
    __tablename__ = 'data_import'

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey('source.id'), index=True)
    status_id = Column(ForeignKey('data_import_status.id'), index=True)
    upload_uuid = Column(String(36))
    filename = Column(Text)
    error_count = Column(Integer)
    warning_count = Column(Integer)
    data_type = Column(Integer, nullable=False)
    time_created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    user_id = Column(ForeignKey('user.id'), index=True)
    source_desc = Column(String(255))

    source = relationship('Source')
    status = relationship('DataImportStatus')
    user = relationship('User')


class DataImportStatus(Base):
    __tablename__ = 'data_import_status'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    code = Column(String(255), nullable=False, unique=True)


class DataProcessingNotes(Base):
    __tablename__ = 'data_processing_notes'

    id = Column(Integer, primary_key=True)
    user_id = Column(ForeignKey('user.id'), nullable=False, index=True)
    source_id = Column(ForeignKey('source.id'), nullable=False, index=True)
    time_created = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    notes = Column(Text, nullable=False)

    source = relationship('Source')
    user = relationship('User')


class DataSource(Base):
    __tablename__ = 'data_source'

    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey('taxon.id'), primary_key=True, nullable=False, index=True)
    data_agreement_id = Column(Integer)
    objective_of_monitoring_id = Column(Integer)
    absences_recorded = Column(Integer)
    standardisation_of_method_effort_id = Column(Integer)
    consistency_of_monitoring_id = Column(Integer)
    exclude_from_analysis = Column(Integer, nullable=False)
    start_year = Column(Integer)
    end_year = Column(Integer)
    suppress_aggregated_data = Column(Integer, nullable=False)

    source = relationship('Source')
    taxon = relationship('Taxon')


class ExperimentalDesignType(Base):
    __tablename__ = 'experimental_design_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class GridCell(Base):
    __tablename__ = 'grid_cell'

    id = Column(Integer, primary_key=True)
    geometry = Column(NullType, nullable=False, index=True)


t_incidental_sighting = Table(
    'incidental_sighting', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('coords', NullType),
    Column('date', Date)
)


class IntensiveManagement(Base):
    __tablename__ = 'intensive_management'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))
    grouping = Column(String(255))


t_processing_method = Table(
    'processing_method', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False),
    Column('unit_id', ForeignKey('unit.id'), index=True),
    Column('source_id', ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True),
    Column('search_type_id', ForeignKey('search_type.id'), index=True),
    Column('data_type', Integer, nullable=False),
    Column('response_variable_type_id', Integer, nullable=False),
    Column('experimental_design_type_id', Integer, nullable=False),
    Column('positional_accuracy_threshold_in_m', Float(asdecimal=True)),
    Index('uniq', 'taxon_id', 'unit_id', 'source_id', 'search_type_id', 'data_type', unique=True)
)


class ProjectionName(Base):
    __tablename__ = 'projection_name'

    name = Column(String(64), primary_key=True)
    epsg_srid = Column(Integer, nullable=False)


class Range(Base):
    __tablename__ = 'range'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class Region(Base):
    __tablename__ = 'region'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    geometry = Column(NullType, nullable=False)
    state = Column(String(255))
    positional_accuracy_in_m = Column(Integer)


t_region_subdiv = Table(
    'region_subdiv', metadata,
    Column('id', Integer, nullable=False),
    Column('name', String(255)),
    Column('geometry', NullType, nullable=False, index=True)
)


class ResponseVariableType(Base):
    __tablename__ = 'response_variable_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False, unique=True)

    users = relationship('User', secondary='user_role')


class SearchType(Base):
    __tablename__ = 'search_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    source_type_id = Column(ForeignKey('source_type.id'), index=True)
    provider = Column(Text)
    description = Column(Text)
    notes = Column(Text)
    authors = Column(Text)
    contact_name = Column(Text)
    contact_institution = Column(Text)
    contact_position = Column(Text)
    contact_email = Column(Text)
    contact_phone = Column(Text)

    source_type = relationship('SourceType')
    users = relationship('User', secondary='user_source')


class SourceType(Base):
    __tablename__ = 'source_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    geometry = Column(NullType)


class T1Sighting(Base):
    __tablename__ = 't1_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey('t1_survey.id', ondelete='CASCADE'), nullable=False, index=True)
    taxon_id = Column(ForeignKey('taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey('unit.id'), nullable=False, index=True)
    breeding = Column(Integer)

    survey = relationship('T1Survey')
    taxon = relationship('Taxon')
    unit = relationship('Unit')


class T1Site(Base):
    __tablename__ = 't1_site'

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey('search_type.id'), nullable=False, index=True)
    notes = Column(Text)
    intensive_management_id = Column(ForeignKey('intensive_management.id'), index=True)

    intensive_management = relationship('IntensiveManagement')
    search_type = relationship('SearchType')
    source = relationship('Source')


class T1Survey(Base):
    __tablename__ = 't1_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey('t1_site.id', ondelete='CASCADE'), nullable=False, index=True)
    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True)
    source_primary_key = Column(String(255), nullable=False, unique=True)
    start_date_d = Column(SmallInteger)
    start_date_m = Column(SmallInteger)
    start_date_y = Column(SmallInteger, nullable=False)
    finish_date_d = Column(SmallInteger)
    finish_date_m = Column(SmallInteger)
    finish_date_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    number_of_traps_per_day = Column(Integer)
    coords = Column(NullType, nullable=False)
    location = Column(Text)
    positional_accuracy_in_m = Column(Float(asdecimal=True))
    comments = Column(Text)

    site = relationship('T1Site')
    source = relationship('Source')


class T2ProcessedSighting(Base):
    __tablename__ = 't2_processed_sighting'
    __table_args__ = (
        Index('survey_id_taxon_id', 'survey_id', 'taxon_id'),
    )

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey('t2_processed_survey.id', ondelete='CASCADE'), nullable=False)
    taxon_id = Column(ForeignKey('taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey('unit.id'), nullable=False, index=True)
    pseudo_absence = Column(Integer, nullable=False)

    survey = relationship('T2ProcessedSurvey')
    taxon = relationship('Taxon')
    unit = relationship('Unit')


class T2ProcessedSurvey(Base):
    __tablename__ = 't2_processed_survey'

    id = Column(Integer, primary_key=True)
    raw_survey_id = Column(ForeignKey('t2_survey.id', ondelete='CASCADE'), nullable=False, index=True)
    site_id = Column(ForeignKey('t2_site.id', ondelete='CASCADE'), index=True)
    grid_cell_id = Column(ForeignKey('grid_cell.id'), index=True)
    search_type_id = Column(Integer, nullable=False)
    start_date_y = Column(SmallInteger, nullable=False)
    start_date_m = Column(SmallInteger)
    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True)
    experimental_design_type_id = Column(Integer)

    grid_cell = relationship('GridCell')
    raw_survey = relationship('T2Survey')
    site = relationship('T2Site')
    source = relationship('Source')


class T2Sighting(Base):
    __tablename__ = 't2_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey('t2_survey.id', ondelete='CASCADE'), nullable=False, index=True)
    taxon_id = Column(ForeignKey('taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True))
    unit_id = Column(ForeignKey('unit.id'), index=True)
    breeding = Column(Integer)

    survey = relationship('T2Survey')
    taxon = relationship('Taxon')
    unit = relationship('Unit')


class T2Site(Base):
    __tablename__ = 't2_site'
    __table_args__ = (
        Index('source_name', 'source_id', 'name'),
    )

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey('search_type.id'), nullable=False, index=True)
    geometry = Column(NullType)

    search_type = relationship('SearchType')
    source = relationship('Source')
    surveys = relationship('T2Survey', secondary='t2_survey_site')


class T2Survey(Base):
    __tablename__ = 't2_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey('t2_site.id', ondelete='CASCADE'), index=True)
    source_id = Column(ForeignKey('source.id', ondelete='CASCADE'), nullable=False, index=True)
    start_date_d = Column(SmallInteger)
    start_date_m = Column(SmallInteger)
    start_date_y = Column(SmallInteger, nullable=False)
    finish_date_d = Column(SmallInteger)
    finish_date_m = Column(SmallInteger)
    finish_date_y = Column(SmallInteger)
    start_time = Column(Time)
    finish_time = Column(Time)
    duration_in_minutes = Column(Integer)
    area_in_m2 = Column(Float(asdecimal=True))
    length_in_km = Column(Float(asdecimal=True))
    coords = Column(NullType, nullable=False, index=True)
    location = Column(Text)
    positional_accuracy_in_m = Column(Float(asdecimal=True))
    comments = Column(Text)
    search_type_id = Column(ForeignKey('search_type.id'), nullable=False, index=True)
    source_primary_key = Column(String(255), nullable=False, unique=True)
    secondary_source_id = Column(String(255))

    search_type = relationship('SearchType')
    site = relationship('T2Site')
    source = relationship('Source')


t_t2_survey_site = Table(
    't2_survey_site', metadata,
    Column('survey_id', ForeignKey('t2_survey.id', ondelete='CASCADE'), primary_key=True, nullable=False),
    Column('site_id', ForeignKey('t2_site.id', ondelete='CASCADE'), primary_key=True, nullable=False, index=True)
)


class T2UltrataxonSighting(Base):
    __tablename__ = 't2_ultrataxon_sighting'

    sighting_id = Column(ForeignKey('t2_sighting.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey('taxon.id'), primary_key=True, nullable=False, index=True)
    range_id = Column(ForeignKey('range.id'), nullable=False, index=True)
    generated_subspecies = Column(Integer, nullable=False)

    range = relationship('Range')
    sighting = relationship('T2Sighting')
    taxon = relationship('Taxon')


class Taxon(Base):
    __tablename__ = 'taxon'

    id = Column(String(8), primary_key=True)
    ultrataxon = Column(Integer, nullable=False)
    taxon_level_id = Column(ForeignKey('taxon_level.id'), index=True)
    spno = Column(SmallInteger)
    common_name = Column(String(255))
    scientific_name = Column(String(255), nullable=False)
    family_common_name = Column(String(255))
    family_scientific_name = Column(String(255))
    order = Column(String(255))
    population = Column(String(255))
    epbc_status_id = Column(ForeignKey('taxon_status.id'), index=True)
    iucn_status_id = Column(ForeignKey('taxon_status.id'), index=True)
    state_status_id = Column(ForeignKey('taxon_status.id'), index=True)
    national_priority = Column(Integer, nullable=False, server_default=text("'0'"))
    taxonomic_group = Column(String(255), nullable=False)
    suppress_spatial_representativeness = Column(Integer, nullable=False, server_default=text("'0'"))

    epbc_status = relationship('TaxonStatus', primaryjoin='Taxon.epbc_status_id == TaxonStatus.id')
    iucn_status = relationship('TaxonStatus', primaryjoin='Taxon.iucn_status_id == TaxonStatus.id')
    state_status = relationship('TaxonStatus', primaryjoin='Taxon.state_status_id == TaxonStatus.id')
    taxon_level = relationship('TaxonLevel')


class TaxonGroup(Base):
    __tablename__ = 'taxon_group'
    __table_args__ = (
        Index('taxon_group_subgroup', 'taxon_id', 'group_name', 'subgroup_name', unique=True),
    )

    id = Column(Integer, primary_key=True)
    taxon_id = Column(ForeignKey('taxon.id'), nullable=False, index=True)
    group_name = Column(String(255), nullable=False)
    subgroup_name = Column(String(255))

    taxon = relationship('Taxon')


class TaxonHybrid(Base):
    __tablename__ = 'taxon_hybrid'

    id = Column(String(12), primary_key=True)
    taxon_id = Column(ForeignKey('taxon.id'), index=True)

    taxon = relationship('Taxon')


class TaxonLevel(Base):
    __tablename__ = 'taxon_level'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


t_taxon_presence_alpha_hull = Table(
    'taxon_presence_alpha_hull', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey('range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False)
)


t_taxon_presence_alpha_hull_subdiv = Table(
    'taxon_presence_alpha_hull_subdiv', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey('range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False, index=True)
)


t_taxon_range = Table(
    'taxon_range', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey('range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey('range.id'), index=True),
    Column('geometry', NullType, nullable=False)
)


t_taxon_range_subdiv = Table(
    'taxon_range_subdiv', metadata,
    Column('taxon_id', ForeignKey('taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey('range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey('range.id'), index=True),
    Column('geometry', NullType, nullable=False, index=True)
)


class TaxonSourceAlphaHull(Base):
    __tablename__ = 'taxon_source_alpha_hull'

    taxon_id = Column(String(8), primary_key=True, nullable=False)
    source_id = Column(Integer, primary_key=True, nullable=False)
    data_type = Column(String(255), primary_key=True, nullable=False)
    geometry = Column(NullType)
    core_range_area_in_m2 = Column(Float(asdecimal=True), nullable=False)
    alpha_hull_area_in_m2 = Column(Float(asdecimal=True))


class TaxonStatus(Base):
    __tablename__ = 'taxon_status'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class TimeSeries(Base):
    __tablename__ = 'time_series'

    id = Column(String(32), primary_key=True)


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    password_hash = Column(Text)
    first_name = Column(Text)
    last_name = Column(Text)
    phone_number = Column(String(32))
    password_reset_code = Column(String(32))


t_user_role = Table(
    'user_role', metadata,
    Column('user_id', ForeignKey('user.id'), primary_key=True, nullable=False),
    Column('role_id', ForeignKey('role.id'), primary_key=True, nullable=False, index=True)
)


t_user_source = Table(
    'user_source', metadata,
    Column('user_id', ForeignKey('user.id'), primary_key=True, nullable=False),
    Column('source_id', ForeignKey('source.id'), primary_key=True, nullable=False, index=True)
)
