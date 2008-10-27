

CREATE TABLE `candidate` (
  `id` char(9) default NULL,
  `name` varchar(38) default NULL,
  `party` char(3) default NULL,
  `party_2` char(3) default NULL,
  `seat_status` char(1) default NULL,
  `status` char(1) default NULL,
  `street_1` varchar(34) default NULL,
  `street_2` varchar(34) default NULL,
  `city` varchar(18) default NULL,
  `state` char(2) default NULL,
  `zipcode` char(5) default NULL,
  `committee_id` char(9) default NULL,
  `election_year` char(2) default NULL,
  `district` char(2) default NULL
);

CREATE TABLE `committee` (
  `id` char(9) default NULL,
  `name` varchar(90) default NULL,
  `treasurer` varchar(38) default NULL,
  `street_1` varchar(34) default NULL,
  `street_2` varchar(34) default NULL,
  `city` varchar(18) default NULL,
  `state` char(2) default NULL,
  `zipcode` char(5) default NULL,
  `designation` char(1) default NULL,
  `type` char(1) default NULL,
  `party` char(3) default NULL,
  `filing_frequency` char(1) default NULL,
  `interest_group_category` char(1) default NULL,
  `connected_org_name` varchar(38) default NULL,
  `candidate_id` char(9) default NULL
);

CREATE TABLE `contribution` (
  `filer_id` char(9) default NULL,
  `amendment` char(1) default NULL,
  `report_type` char(3) default NULL,
  `primary_general` char(1) default NULL,
  `microfilm_loc` char(11) default NULL,
  `transaction_type` char(3) default NULL,
  `name` varchar(34) default NULL,
  `city` varchar(18) default NULL,
  `state` char(2) default NULL,
  `zipcode` char(5) default NULL,
  `occupation` varchar(35) default NULL,
  `month` char(2) default NULL,
  `day` char(2) default NULL,
  `year` char(4) default NULL,
  `amount` char(7) default NULL,
  `other_id` char(9) default NULL,
  `fec_record_number` char(7) default NULL
) ;
