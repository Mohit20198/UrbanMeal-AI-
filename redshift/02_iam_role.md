# AWS IAM Role Setup for Amazon Redshift

To allow Amazon Redshift to load files directly from your Amazon S3 bucket, Redshift needs an IAM role with S3 read access attached to your Redshift cluster or Serverless namespace.

---

### Step 1: Create the IAM Role in AWS IAM Console

1. Open the [AWS IAM Console](https://console.aws.amazon.com/iam/).
2. In the navigation pane, click **Roles** -> **Create role**.
3. Under **Trusted entity type**, select **AWS service**.
4. Under **Use case**, select **Redshift**, then select **Redshift - Customizable** (or simply choose Redshift).
   *(This applies the trust policy for `redshift.amazonaws.com` as defined in `aws/iam/redshift-role-trust-policy.json`)*.
5. Click **Next**.
6. Under **Add permissions**, attach:
   - **`AmazonS3ReadOnlyAccess`** (managed policy)
   - OR create an inline policy using `aws/iam/s3-read-policy.json` (replacing `<BUCKET>` with your S3 bucket name).
7. Name the role: **`redshift-urbanmeal-role`**.
8. Click **Create role**.
9. Copy the **Role ARN** (e.g. `arn:aws:iam::123456789012:role/redshift-urbanmeal-role`).

---

### Step 2: Attach the IAM Role to Amazon Redshift

#### If using **Amazon Redshift Serverless**:
1. Go to the [Amazon Redshift Console](https://console.aws.amazon.com/redshiftv2/).
2. In the left navigation, click **Redshift Serverless** -> **Namespace configuration**.
3. Select your namespace (e.g., `default`).
4. In the **Security and encryption** tab, click **Manage IAM roles**.
5. Click **Associate IAM roles**, select **`redshift-urbanmeal-role`**, and click **Associate IAM roles**.

#### If using **Amazon Redshift Provisioned Cluster**:
1. Go to **Clusters** in the Redshift Console and select your cluster.
2. Click **Actions** -> **Manage IAM roles**.
3. Select **`redshift-urbanmeal-role`** and click **Associate IAM role**.
4. Click **Save changes**.

---

### Step 3: Verify the Role ARN
Your configured Role ARN is:
```text
arn:aws:iam::<your-account-id>:role/redshift-urbanmeal-role
```
It is already linked and configured in:
- `redshift/04_copy_into.sql`
- `airflow/example.env` (`REDSHIFT_ROLE_ARN`)
- `airflow/dags/urbanmeal_batch.py`
