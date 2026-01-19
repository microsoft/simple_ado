"""Defines the built-in work item fields for Azure DevOps (ADO)."""

import enum


class ADOWorkItemBuiltInFields(enum.Enum):
    """Defines the various built-in work item fields."""

    # The build in which the bug was found
    FOUND_IN = "Microsoft.VSTS.Build.FoundIn"
    # The build in which the bug was fixed
    INTEGRATION_BUILD = "Microsoft.VSTS.Build.IntegrationBuild"
    ACTUAL_ATTENDEE_1 = "Microsoft.VSTS.CMMI.ActualAttendee1"
    ACTUAL_ATTENDEE_2 = "Microsoft.VSTS.CMMI.ActualAttendee2"
    ACTUAL_ATTENDEE_3 = "Microsoft.VSTS.CMMI.ActualAttendee3"
    ACTUAL_ATTENDEE_4 = "Microsoft.VSTS.CMMI.ActualAttendee4"
    ACTUAL_ATTENDEE_5 = "Microsoft.VSTS.CMMI.ActualAttendee5"
    ACTUAL_ATTENDEE_6 = "Microsoft.VSTS.CMMI.ActualAttendee6"
    ACTUAL_ATTENDEE_7 = "Microsoft.VSTS.CMMI.ActualAttendee7"
    ACTUAL_ATTENDEE_8 = "Microsoft.VSTS.CMMI.ActualAttendee8"
    # The analysis of the issue including root cause identification and potential solutions
    ANALYSIS = "Microsoft.VSTS.CMMI.Analysis"
    BLOCKED = "Microsoft.VSTS.CMMI.Blocked"
    # The person who called the review
    CALLED_BY = "Microsoft.VSTS.CMMI.CalledBy"
    # The date and time the review was called
    CALLED_DATE = "Microsoft.VSTS.CMMI.CalledDate"
    # Comments for the review
    COMMENTS = "Microsoft.VSTS.CMMI.Comments"
    # Has the requirement been committed?
    COMMITTED = "Microsoft.VSTS.CMMI.Committed"
    CONTINGENCY_PLAN = "Microsoft.VSTS.CMMI.ContingencyPlan"
    CORRECTIVE_ACTION_ACTUAL_RESOLUTION = "Microsoft.VSTS.CMMI.CorrectiveActionActualResolution"
    CORRECTIVE_ACTION_PLAN = "Microsoft.VSTS.CMMI.CorrectiveActionPlan"
    # Used to flag an issue as critical
    ESCALATE = "Microsoft.VSTS.CMMI.Escalate"
    FOUND_IN_ENVIRONMENT = "Microsoft.VSTS.CMMI.FoundInEnvironment"
    HOW_FOUND = "Microsoft.VSTS.CMMI.HowFound"
    IMPACT_ASSESSMENT_HTML = "Microsoft.VSTS.CMMI.ImpactAssessmentHtml"
    IMPACT_ON_ARCHITECTURE = "Microsoft.VSTS.CMMI.ImpactOnArchitecture"
    IMPACT_ON_DEVELOPMENT = "Microsoft.VSTS.CMMI.ImpactOnDevelopment"
    IMPACT_ON_TECHNICAL_PUBLICATIONS = "Microsoft.VSTS.CMMI.ImpactOnTechnicalPublications"
    IMPACT_ON_TEST = "Microsoft.VSTS.CMMI.ImpactOnTest"
    IMPACT_ON_USER_EXPERIENCE = "Microsoft.VSTS.CMMI.ImpactOnUserExperience"
    JUSTIFICATION = "Microsoft.VSTS.CMMI.Justification"
    # The type of the review meeting
    MEETING_TYPE = "Microsoft.VSTS.CMMI.MeetingType"
    # The minutes of the review meeting
    MINUTES = "Microsoft.VSTS.CMMI.Minutes"
    MITIGATION_PLAN = "Microsoft.VSTS.CMMI.MitigationPlan"
    # The mitigation triggers
    MITIGATION_TRIGGERS = "Microsoft.VSTS.CMMI.MitigationTriggers"
    OPTIONAL_ATTENDEE_1 = "Microsoft.VSTS.CMMI.OptionalAttendee1"
    OPTIONAL_ATTENDEE_2 = "Microsoft.VSTS.CMMI.OptionalAttendee2"
    OPTIONAL_ATTENDEE_3 = "Microsoft.VSTS.CMMI.OptionalAttendee3"
    OPTIONAL_ATTENDEE_4 = "Microsoft.VSTS.CMMI.OptionalAttendee4"
    OPTIONAL_ATTENDEE_5 = "Microsoft.VSTS.CMMI.OptionalAttendee5"
    OPTIONAL_ATTENDEE_6 = "Microsoft.VSTS.CMMI.OptionalAttendee6"
    OPTIONAL_ATTENDEE_7 = "Microsoft.VSTS.CMMI.OptionalAttendee7"
    OPTIONAL_ATTENDEE_8 = "Microsoft.VSTS.CMMI.OptionalAttendee8"
    # A percentage indicating the estimated likelihood that the risk will occur
    PROBABILITY = "Microsoft.VSTS.CMMI.Probability"
    PROPOSED_FIX = "Microsoft.VSTS.CMMI.ProposedFix"
    # The purpose of the review
    PURPOSE = "Microsoft.VSTS.CMMI.Purpose"
    REQUIRED_ATTENDEE_1 = "Microsoft.VSTS.CMMI.RequiredAttendee1"
    REQUIRED_ATTENDEE_2 = "Microsoft.VSTS.CMMI.RequiredAttendee2"
    REQUIRED_ATTENDEE_3 = "Microsoft.VSTS.CMMI.RequiredAttendee3"
    REQUIRED_ATTENDEE_4 = "Microsoft.VSTS.CMMI.RequiredAttendee4"
    REQUIRED_ATTENDEE_5 = "Microsoft.VSTS.CMMI.RequiredAttendee5"
    REQUIRED_ATTENDEE_6 = "Microsoft.VSTS.CMMI.RequiredAttendee6"
    REQUIRED_ATTENDEE_7 = "Microsoft.VSTS.CMMI.RequiredAttendee7"
    REQUIRED_ATTENDEE_8 = "Microsoft.VSTS.CMMI.RequiredAttendee8"
    REQUIREMENT_TYPE = "Microsoft.VSTS.CMMI.RequirementType"
    REQUIRES_REVIEW = "Microsoft.VSTS.CMMI.RequiresReview"
    REQUIRES_TEST = "Microsoft.VSTS.CMMI.RequiresTest"
    ROOT_CAUSE = "Microsoft.VSTS.CMMI.RootCause"
    SUBJECT_MATTER_EXPERT_1 = "Microsoft.VSTS.CMMI.SubjectMatterExpert1"
    SUBJECT_MATTER_EXPERT_2 = "Microsoft.VSTS.CMMI.SubjectMatterExpert2"
    SUBJECT_MATTER_EXPERT_3 = "Microsoft.VSTS.CMMI.SubjectMatterExpert3"
    SYMPTOM = "Microsoft.VSTS.CMMI.Symptom"
    TARGET_RESOLVE_DATE = "Microsoft.VSTS.CMMI.TargetResolveDate"
    TASK_TYPE = "Microsoft.VSTS.CMMI.TaskType"
    USER_ACCEPTANCE_TEST = "Microsoft.VSTS.CMMI.UserAcceptanceTest"
    ACCEPTED_BY = "Microsoft.VSTS.CodeReview.AcceptedBy"
    ACCEPTED_DATE = "Microsoft.VSTS.CodeReview.AcceptedDate"
    CLOSED_STATUS = "Microsoft.VSTS.CodeReview.ClosedStatus"
    CLOSED_STATUS_CODE = "Microsoft.VSTS.CodeReview.ClosedStatusCode"
    CLOSING_COMMENT = "Microsoft.VSTS.CodeReview.ClosingComment"
    ASSOCIATED_CONTEXT = "Microsoft.VSTS.CodeReview.Context"
    ASSOCIATED_CONTEXT_CODE = "Microsoft.VSTS.CodeReview.ContextCode"
    ASSOCIATED_CONTEXT_OWNER = "Microsoft.VSTS.CodeReview.ContextOwner"
    ASSOCIATED_CONTEXT_TYPE = "Microsoft.VSTS.CodeReview.ContextType"
    ACCEPTANCE_CRITERIA = "Microsoft.VSTS.Common.AcceptanceCriteria"
    ACTIVATED_BY = "Microsoft.VSTS.Common.ActivatedBy"
    ACTIVATED_DATE = "Microsoft.VSTS.Common.ActivatedDate"
    # Type of work involved
    ACTIVITY = "Microsoft.VSTS.Common.Activity"
    BACKLOG_PRIORITY = "Microsoft.VSTS.Common.BacklogPriority"
    # The business value for the customer when the epic is released
    BUSINESS_VALUE = "Microsoft.VSTS.Common.BusinessValue"
    CLOSED_BY = "Microsoft.VSTS.Common.ClosedBy"
    CLOSED_DATE = "Microsoft.VSTS.Common.ClosedDate"
    # The discipline to which the bug belongs
    DISCIPLINE = "Microsoft.VSTS.Common.Discipline"
    # Used to highlight the shared step, e.g., to mark it as an issue
    ISSUE = "Microsoft.VSTS.Common.Issue"
    # Business importance. 1=must fix; 4=unimportant.
    PRIORITY = "Microsoft.VSTS.Common.Priority"
    # Overall rating provided as part of feedback response
    RATING = "Microsoft.VSTS.Common.Rating"
    RESOLUTION = "Microsoft.VSTS.Common.Resolution"
    RESOLVED_BY = "Microsoft.VSTS.Common.ResolvedBy"
    RESOLVED_DATE = "Microsoft.VSTS.Common.ResolvedDate"
    # The reason why the bug was resolved
    RESOLVED_REASON = "Microsoft.VSTS.Common.ResolvedReason"
    REVIEWED_BY = "Microsoft.VSTS.Common.ReviewedBy"
    # Uncertainty in epic
    RISK = "Microsoft.VSTS.Common.Risk"
    # Assessment of the effect of the bug on the project
    SEVERITY = "Microsoft.VSTS.Common.Severity"
    # Work first on items with lower-valued stack rank. Set in triage.
    STACK_RANK = "Microsoft.VSTS.Common.StackRank"
    STATE_CHANGE_DATE = "Microsoft.VSTS.Common.StateChangeDate"
    STATE_CODE = "Microsoft.VSTS.Common.StateCode"
    # How does the business value decay over time. Higher values make the epic more time critical
    TIME_CRITICALITY = "Microsoft.VSTS.Common.TimeCriticality"
    # Status of triaging the bug
    TRIAGE = "Microsoft.VSTS.Common.Triage"
    # The type should be set to Business primarily to represent customer-facing issues. Work to
    # change the architecture should be added as a User Story
    VALUE_AREA = "Microsoft.VSTS.Common.ValueArea"
    # Instructions to launch the specified application
    APPLICATION_LAUNCH_INSTRUCTIONS = "Microsoft.VSTS.Feedback.ApplicationLaunchInstructions"
    # The path to execute the application
    APPLICATION_START_INFORMATION = "Microsoft.VSTS.Feedback.ApplicationStartInformation"
    # The type of application on which to give feedback
    APPLICATION_TYPE = "Microsoft.VSTS.Feedback.ApplicationType"
    # The number of units of work that have been spent on this bug
    COMPLETED_WORK = "Microsoft.VSTS.Scheduling.CompletedWork"
    # The date by which this issue needs to be closed
    DUE_DATE = "Microsoft.VSTS.Scheduling.DueDate"
    # The estimated effort to implemented the epic
    EFFORT = "Microsoft.VSTS.Scheduling.Effort"
    # The date to finish the task
    FINISH_DATE = "Microsoft.VSTS.Scheduling.FinishDate"
    # Initial value for Remaining Work - set once, when work begins
    ORIGINAL_ESTIMATE = "Microsoft.VSTS.Scheduling.OriginalEstimate"
    # An estimate of the number of units of work remaining to complete this bug
    REMAINING_WORK = "Microsoft.VSTS.Scheduling.RemainingWork"
    # The size of work estimated for fixing the bug
    SIZE = "Microsoft.VSTS.Scheduling.Size"
    # The date to start the task
    START_DATE = "Microsoft.VSTS.Scheduling.StartDate"
    # The size of work estimated for fixing the bug
    STORY_POINTS = "Microsoft.VSTS.Scheduling.StoryPoints"
    # The target date for completing the epic
    TARGET_DATE = "Microsoft.VSTS.Scheduling.TargetDate"
    # The ID of the test that automates this test case
    AUTOMATED_TEST_ID = "Microsoft.VSTS.TCM.AutomatedTestId"
    # The name of the test that automates this test case
    AUTOMATED_TEST_NAME = "Microsoft.VSTS.TCM.AutomatedTestName"
    # The assembly containing the test that automates this test case
    AUTOMATED_TEST_STORAGE = "Microsoft.VSTS.TCM.AutomatedTestStorage"
    # The type of the test that automates this test case
    AUTOMATED_TEST_TYPE = "Microsoft.VSTS.TCM.AutomatedTestType"
    AUTOMATION_STATUS = "Microsoft.VSTS.TCM.AutomationStatus"
    LOCAL_DATA_SOURCE = "Microsoft.VSTS.TCM.LocalDataSource"
    PARAMETERS = "Microsoft.VSTS.TCM.Parameters"
    QUERY_TEXT = "Microsoft.VSTS.TCM.QueryText"
    # How to see the bug. End by contrasting expected with actual behavior.
    REPRO_STEPS = "Microsoft.VSTS.TCM.ReproSteps"
    # Steps required to perform the test
    STEPS = "Microsoft.VSTS.TCM.Steps"
    # Test context, provided automatically by test infrastructure
    SYSTEM_INFO = "Microsoft.VSTS.TCM.SystemInfo"
    # Captures the test suite audit trail.
    TEST_SUITE_AUDIT = "Microsoft.VSTS.TCM.TestSuiteAudit"
    # Specifies the category of the test suite.
    TEST_SUITE_TYPE = "Microsoft.VSTS.TCM.TestSuiteType"
    TEST_SUITE_TYPE_ID = "Microsoft.VSTS.TCM.TestSuiteTypeId"
    AREA_ID = "System.AreaId"
    AREA_LEVEL_1 = "System.AreaLevel1"
    AREA_LEVEL_2 = "System.AreaLevel2"
    AREA_LEVEL_3 = "System.AreaLevel3"
    AREA_LEVEL_4 = "System.AreaLevel4"
    AREA_LEVEL_5 = "System.AreaLevel5"
    AREA_LEVEL_6 = "System.AreaLevel6"
    AREA_LEVEL_7 = "System.AreaLevel7"
    # The area of the product with which this bug is associated
    AREA_PATH = "System.AreaPath"
    # The person currently working on this bug
    ASSIGNED_TO = "System.AssignedTo"
    ATTACHED_FILE_COUNT = "System.AttachedFileCount"
    ATTACHED_FILES = "System.AttachedFiles"
    AUTHORIZED_AS = "System.AuthorizedAs"
    AUTHORIZED_DATE = "System.AuthorizedDate"
    BIS_LINKS = "System.BISLinks"
    BOARD_COLUMN = "System.BoardColumn"
    BOARD_COLUMN_DONE = "System.BoardColumnDone"
    BOARD_LANE = "System.BoardLane"
    CHANGED_BY = "System.ChangedBy"
    CHANGED_DATE = "System.ChangedDate"
    COMMENT_COUNT = "System.CommentCount"
    CREATED_BY = "System.CreatedBy"
    CREATED_DATE = "System.CreatedDate"
    # Description or acceptance criteria for this epic to be considered complete
    DESCRIPTION = "System.Description"
    EXTERNAL_LINK_COUNT = "System.ExternalLinkCount"
    # Discussion thread plus automatic record of changes
    HISTORY = "System.History"
    HYPERLINK_COUNT = "System.HyperLinkCount"
    ID = "System.Id"
    IN_ADMIN_ONLY_TREE_FLAG = "System.InAdminOnlyTreeFlag"
    IN_DELETED_TREE_FLAG = "System.InDeletedTreeFlag"
    IS_DELETED = "System.IsDeleted"
    ITERATION_ID = "System.IterationId"
    ITERATION_LEVEL_1 = "System.IterationLevel1"
    ITERATION_LEVEL_2 = "System.IterationLevel2"
    ITERATION_LEVEL_3 = "System.IterationLevel3"
    ITERATION_LEVEL_4 = "System.IterationLevel4"
    ITERATION_LEVEL_5 = "System.IterationLevel5"
    ITERATION_LEVEL_6 = "System.IterationLevel6"
    ITERATION_LEVEL_7 = "System.IterationLevel7"
    # The iteration within which this bug will be fixed
    ITERATION_PATH = "System.IterationPath"
    LINKED_FILES = "System.LinkedFiles"
    LINK_TYPE = "System.Links.LinkType"
    NODE_NAME = "System.NodeName"
    NODE_TYPE = "System.NodeType"
    PARENT = "System.Parent"
    PERSON_ID = "System.PersonId"
    PROJECT_ID = "System.ProjectId"
    # The reason why the bug is in the current state
    REASON = "System.Reason"
    RELATED_LINK_COUNT = "System.RelatedLinkCount"
    RELATED_LINKS = "System.RelatedLinks"
    REMOTE_LINK_COUNT = "System.RemoteLinkCount"
    REV = "System.Rev"
    REVISED_DATE = "System.RevisedDate"
    # New = for triage; Active = not yet fixed; Resolved = fixed not yet verified;
    # Closed = fix verified.
    STATE = "System.State"
    TAGS = "System.Tags"
    TEAM_PROJECT = "System.TeamProject"
    TF_SERVER = "System.TFServer"
    # Stories affected and how
    TITLE = "System.Title"
    WATERMARK = "System.Watermark"
    WORK_ITEM_FORM = "System.WorkItemForm"
    WORK_ITEM_FORM_ID = "System.WorkItemFormId"
    WORK_ITEM_TYPE = "System.WorkItemType"
