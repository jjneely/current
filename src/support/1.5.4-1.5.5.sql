alter table rpmprovide rename to oldprovide;
create table rpmprovide (
    rpmprovide_id   int default nextval('rpmprovide_id_seq') unique not null,
    rpm_id          int not null,
    name            varchar(4096),
    flags           varchar(64),
    vers            varchar(64)
    );
drop index rpmprovide_id_idx;
drop index rpmprovide_rpm_id_idx;
insert into rpmprovide select * from oldprovide;
drop table oldprovide;
create index RPMPROVIDE_ID_IDX on RPMPROVIDE(rpmprovide_id);
create index RPMPROVIDE_RPM_ID_IDX on RPMPROVIDE(rpm_id);
