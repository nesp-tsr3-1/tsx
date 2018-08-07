# coding: utf-8
from sqlalchemy import Column, Date, Float, ForeignKey, Index, Integer, SmallInteger, String, Table, Text, Time, text
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
    Column('grid_cell_id', ForeignKey(u'grid_cell.id'), index=True),
    Column('search_type_id', ForeignKey(u'search_type.id'), index=True),
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('experimental_design_type_id', ForeignKey(u'experimental_design_type.id'), nullable=False, index=True),
    Column('response_variable_type_id', ForeignKey(u'response_variable_type.id'), nullable=False, index=True),
    Column('value', Float(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True),
    Column('region_id', ForeignKey(u'region.id'), index=True),
    Column('unit_id', ForeignKey(u'unit.id'), nullable=False, index=True),
    Column('positional_accuracy_in_m', Float(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32))
)


t_aggregated_by_year = Table(
    'aggregated_by_year', metadata,
    Column('start_date_y', SmallInteger, nullable=False),
    Column('site_id', Integer),
    Column('grid_cell_id', ForeignKey(u'grid_cell.id'), index=True),
    Column('search_type_id', ForeignKey(u'search_type.id'), index=True),
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('experimental_design_type_id', ForeignKey(u'experimental_design_type.id'), nullable=False, index=True),
    Column('response_variable_type_id', ForeignKey(u'response_variable_type.id'), nullable=False, index=True),
    Column('value', Float(asdecimal=True), nullable=False),
    Column('data_type', Integer, nullable=False),
    Column('source_id', ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True),
    Column('region_id', ForeignKey(u'region.id'), index=True),
    Column('unit_id', ForeignKey(u'unit.id'), nullable=False, index=True),
    Column('positional_accuracy_in_m', Float(asdecimal=True)),
    Column('centroid_coords', NullType, nullable=False),
    Column('survey_count', Integer, nullable=False),
    Column('time_series_id', String(32)),
    Column('include_in_analysis', Integer, nullable=False, server_default=text("'0'"))
)


class DataSource(Base):
    __tablename__ = 'data_source'

    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey(u'taxon.id'), primary_key=True, nullable=False, index=True)
    data_agreement_id = Column(Integer)
    objective_of_monitoring_id = Column(Integer)
    absences_recorded = Column(Integer)
    standardisation_of_method_effort_id = Column(Integer)
    consistency_of_monitoring_id = Column(Integer)

    source = relationship(u'Source')
    taxon = relationship(u'Taxon')


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
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('coords', NullType),
    Column('date', Date)
)


t_processing_method = Table(
    'processing_method', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False),
    Column('unit_id', ForeignKey(u'unit.id'), index=True),
    Column('source_id', ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True),
    Column('search_type_id', ForeignKey(u'search_type.id'), index=True),
    Column('data_type', Integer, nullable=False),
    Column('response_variable_type_id', Integer, nullable=False),
    Column('experimental_design_type_id', Integer, nullable=False),
    Column('positional_accuracy_threshold_in_m', Float(asdecimal=True)),
    Index('uniq', 'taxon_id', 'unit_id', 'source_id', 'search_type_id', 'data_type', unique=True)
)


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


class SearchType(Base):
    __tablename__ = 'search_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class Source(Base):
    __tablename__ = 'source'

    id = Column(Integer, primary_key=True)
    source_type_id = Column(ForeignKey(u'source_type.id'), index=True)
    provider = Column(String(255))
    description = Column(Text)
    notes = Column(Text)
    authors = Column(Text)

    source_type = relationship(u'SourceType')


class SourceType(Base):
    __tablename__ = 'source_type'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


class SpeciesRange(Base):
    __tablename__ = 'species_range'

    species_id = Column(Integer, primary_key=True)


class State(Base):
    __tablename__ = 'state'

    id = Column(Integer, primary_key=True)
    name = Column(String(255))
    geometry = Column(NullType)


class T1Sighting(Base):
    __tablename__ = 't1_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't1_survey.id', ondelete=u'CASCADE'), nullable=False, index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey(u'unit.id'), nullable=False, index=True)
    breeding = Column(Integer)

    survey = relationship(u'T1Survey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T1Site(Base):
    __tablename__ = 't1_site'

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    notes = Column(Text)

    search_type = relationship(u'SearchType')
    source = relationship(u'Source')


class T1Survey(Base):
    __tablename__ = 't1_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey(u't1_site.id', ondelete=u'CASCADE'), nullable=False, index=True)
    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True)
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
    coords = Column(NullType, nullable=False)
    location = Column(Text)
    positional_accuracy_in_m = Column(Float(asdecimal=True))
    comments = Column(Text)

    site = relationship(u'T1Site')
    source = relationship(u'Source')


class T2ProcessedSighting(Base):
    __tablename__ = 't2_processed_sighting'
    __table_args__ = (
        Index('survey_id_taxon_id', 'survey_id', 'taxon_id'),
    )

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't2_processed_survey.id', ondelete=u'CASCADE'), nullable=False)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True), nullable=False)
    unit_id = Column(ForeignKey(u'unit.id'), nullable=False, index=True)
    pseudo_absence = Column(Integer, nullable=False)

    survey = relationship(u'T2ProcessedSurvey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T2ProcessedSurvey(Base):
    __tablename__ = 't2_processed_survey'

    id = Column(Integer, primary_key=True)
    raw_survey_id = Column(ForeignKey(u't2_survey.id', ondelete=u'CASCADE'), nullable=False, index=True)
    site_id = Column(ForeignKey(u't2_site.id', ondelete=u'CASCADE'), index=True)
    grid_cell_id = Column(ForeignKey(u'grid_cell.id'), index=True)
    search_type_id = Column(Integer, nullable=False)
    start_date_y = Column(SmallInteger, nullable=False)
    start_date_m = Column(SmallInteger)
    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True)
    experimental_design_type_id = Column(Integer)

    grid_cell = relationship(u'GridCell')
    raw_survey = relationship(u'T2Survey')
    site = relationship(u'T2Site')
    source = relationship(u'Source')


class T2Sighting(Base):
    __tablename__ = 't2_sighting'

    id = Column(Integer, primary_key=True)
    survey_id = Column(ForeignKey(u't2_survey.id', ondelete=u'CASCADE'), nullable=False, index=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), nullable=False, index=True)
    count = Column(Float(asdecimal=True))
    unit_id = Column(ForeignKey(u'unit.id'), index=True)
    breeding = Column(Integer)

    survey = relationship(u'T2Survey')
    taxon = relationship(u'Taxon')
    unit = relationship(u'Unit')


class T2Site(Base):
    __tablename__ = 't2_site'
    __table_args__ = (
        Index('source_name', 'source_id', 'name'),
    )

    id = Column(Integer, primary_key=True)
    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), index=True)
    name = Column(String(255))
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    geometry = Column(NullType)

    search_type = relationship(u'SearchType')
    source = relationship(u'Source')
    surveys = relationship(u'T2Survey', secondary='t2_survey_site')


class T2Survey(Base):
    __tablename__ = 't2_survey'

    id = Column(Integer, primary_key=True)
    site_id = Column(ForeignKey(u't2_site.id', ondelete=u'CASCADE'), index=True)
    source_id = Column(ForeignKey(u'source.id', ondelete=u'CASCADE'), nullable=False, index=True)
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
    search_type_id = Column(ForeignKey(u'search_type.id'), nullable=False, index=True)
    source_primary_key = Column(String(255), nullable=False, unique=True)
    secondary_source_id = Column(String(255))

    search_type = relationship(u'SearchType')
    site = relationship(u'T2Site')
    source = relationship(u'Source')


t_t2_survey_site = Table(
    't2_survey_site', metadata,
    Column('survey_id', ForeignKey(u't2_survey.id', ondelete=u'CASCADE'), primary_key=True, nullable=False),
    Column('site_id', ForeignKey(u't2_site.id', ondelete=u'CASCADE'), primary_key=True, nullable=False, index=True)
)


class T2UltrataxonSighting(Base):
    __tablename__ = 't2_ultrataxon_sighting'

    sighting_id = Column(ForeignKey(u't2_sighting.id', ondelete=u'CASCADE'), primary_key=True, nullable=False)
    taxon_id = Column(ForeignKey(u'taxon.id'), primary_key=True, nullable=False, index=True)
    range_id = Column(ForeignKey(u'range.id'), nullable=False, index=True)
    generated_subspecies = Column(Integer, nullable=False)

    range = relationship(u'Range')
    sighting = relationship(u'T2Sighting')
    taxon = relationship(u'Taxon')


class Taxon(Base):
    __tablename__ = 'taxon'

    id = Column(String(6), primary_key=True)
    ultrataxon = Column(Integer, nullable=False)
    taxon_level_id = Column(ForeignKey(u'taxon_level.id'), nullable=False, index=True)
    spno = Column(SmallInteger, nullable=False)
    common_name = Column(String(255), nullable=False)
    scientific_name = Column(String(255), nullable=False)
    family_common_name = Column(String(255))
    family_scientific_name = Column(String(255))
    order = Column(String(255))
    population = Column(String(255))
    aust_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    epbc_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    iucn_status_id = Column(ForeignKey(u'taxon_status.id'), index=True)
    bird_group = Column(String(255))
    bird_sub_group = Column(String(255))
    national_priority = Column(Integer, nullable=False, server_default=text("'0'"))
    taxonomic_group = Column(String(255))

    aust_status = relationship(u'TaxonStatus', primaryjoin='Taxon.aust_status_id == TaxonStatus.id')
    epbc_status = relationship(u'TaxonStatus', primaryjoin='Taxon.epbc_status_id == TaxonStatus.id')
    iucn_status = relationship(u'TaxonStatus', primaryjoin='Taxon.iucn_status_id == TaxonStatus.id')
    taxon_level = relationship(u'TaxonLevel')


class TaxonHybrid(Base):
    __tablename__ = 'taxon_hybrid'

    id = Column(String(12), primary_key=True)
    taxon_id = Column(ForeignKey(u'taxon.id'), index=True)

    taxon = relationship(u'Taxon')


class TaxonLevel(Base):
    __tablename__ = 'taxon_level'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)


t_taxon_presence_alpha_hull = Table(
    'taxon_presence_alpha_hull', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False)
)


t_taxon_presence_alpha_hull_subdiv = Table(
    'taxon_presence_alpha_hull_subdiv', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', Integer),
    Column('geometry', NullType, nullable=False, index=True)
)


t_taxon_range = Table(
    'taxon_range', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey(u'range.id'), index=True),
    Column('geometry', NullType, nullable=False)
)


t_taxon_range_subdiv = Table(
    'taxon_range_subdiv', metadata,
    Column('taxon_id', ForeignKey(u'taxon.id'), nullable=False, index=True),
    Column('range_id', ForeignKey(u'range.id'), nullable=False, index=True),
    Column('breeding_range_id', ForeignKey(u'range.id'), index=True),
    Column('geometry', NullType, nullable=False, index=True)
)


class TaxonSourceAlphaHull(Base):
    __tablename__ = 'taxon_source_alpha_hull'

    taxon_id = Column(String(6), primary_key=True, nullable=False)
    source_id = Column(Integer, primary_key=True, nullable=False)
    data_type = Column(String(255), primary_key=True, nullable=False)
    geometry = Column(NullType)
    core_range_area_in_m2 = Column(Float(asdecimal=True), nullable=False)
    alpha_hull_area_in_m2 = Column(Float(asdecimal=True))


class TaxonStatus(Base):
    __tablename__ = 'taxon_status'

    id = Column(Integer, primary_key=True)
    description = Column(String(255))


class Unit(Base):
    __tablename__ = 'unit'

    id = Column(Integer, primary_key=True)
    description = Column(String(255), nullable=False)
