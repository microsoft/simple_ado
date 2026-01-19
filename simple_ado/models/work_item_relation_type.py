"""Defines the various relationship types between work items in Azure DevOps (ADO)."""

import enum


class WorkItemRelationType(enum.Enum):
    """Defines the various relationship types between work items."""

    PRODUCES_FOR = "System.LinkTypes.Remote.Dependency-Forward"
    CONSUMES_FROM = "System.LinkTypes.Remote.Dependency-Reverse"

    DUPLICATE = "System.LinkTypes.Duplicate-Forward"
    DUPLICATE_OF = "System.LinkTypes.Duplicate-Reverse"

    BLOCKED_BY = "Microsoft.VSTS.BlockingLink-Forward"
    BLOCKING = "Microsoft.VSTS.BlockingLink-Reverse"

    REFERENCED_BY = "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Forward"
    REFERENCES = "Microsoft.VSTS.TestCase.SharedParameterReferencedBy-Reverse"

    TESTED_BY = "Microsoft.VSTS.Common.TestedBy-Forward"
    TESTS = "Microsoft.VSTS.Common.TestedBy-Reverse"

    TEST_CASE = "Microsoft.VSTS.TestCase.SharedStepReferencedBy-Forward"
    SHARED_STEPS = "Microsoft.VSTS.TestCase.SharedStepReferencedBy-Reverse"

    SUCCESSOR = "System.LinkTypes.Dependency-Forward"
    PREDECESSOR = "System.LinkTypes.Dependency-Reverse"

    CHILD = "System.LinkTypes.Hierarchy-Forward"
    PARENT = "System.LinkTypes.Hierarchy-Reverse"

    REMOTE_RELATED = "System.LinkTypes.Remote.Related"
    RELATED = "System.LinkTypes.Related"

    ATTACHED_FILE = "AttachedFile"

    HYPERLINK = "Hyperlink"

    ARTIFACT_LINK = "ArtifactLink"
